#!/usr/bin/env python
from optparse import OptionParser
import os, sys, re
import subprocess

class ExecutionError(Exception):
    
    def __init__(self, title, message):
        self.title = title
        self.message = message


'''
Repository management tool.

Please try to keep the code cross-OS compatible: Windows and Linux. 
'''

def show_help():
    print '''Usage: python %s [OPTIONS] COMMAND

 Commands:
     
     pull
         Pulls the content from the hg and github repositories
         Fixes the file permissions.
         Runs South migrations.
         Validates the code.
         Touches wsgi.
    
     diff
         Lists the difference across all repos
         
     hgsub
         Update .hgsubstate
         
     cs
         Collectstatic
        
     st
         status
         
Options:

     -a --automatic
         no interaction or user input required

     -e --email=EMAIL_ADDRESS
         send error message to EMAIL_ADDRESS

    ''' % os.path.basename(__file__)
    exit

def get_allowed_branch_names():
    return ['master', 'staging', 'ref2014']

def get_allowed_branch_names_as_str():
    return '|'.join(get_allowed_branch_names())

def get_hg_folder_name():
    ret = ''
    for root, dirs, files in os.walk('.'):
        if 'settings.py' in files: 
            ret = root
            break
    return ret

def process_commands():
    dir = os.getcwd()
    
    parent_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
    os.chdir(parent_dir)
    
    try:
        process_commands_main_dir()
    finally:
        os.chdir(dir)
        
def process_commands_main_dir():
    parser = OptionParser()
    parser.add_option("-a", "--automatic",
                      action="store_true", dest="automatic", default=False,
                      help="no input necessary")
    parser.add_option("-e", "--email",
                      action="store", dest="email", default='',
                      help="email to send errors to")
    
    (options, args) = parser.parse_args()
    
    known_command = False
    
    if len(args):
        command = args[0]
        dir = os.getcwd()
        
        if command == 'st':
            known_command = True
            
            try:
                out = {}

                # GIT
                os.chdir('digipal')
                system('git status', '', False, '', out)
                
                branch = re.sub(ur'(?musi)^.*on branch (\S+).*$', ur'\1', out['output'])
                has_local_change = (out['output'].find('modified:') > -1)
                
                status = branch
                if has_local_change:
                    status += ' (%s)' % 'LOCAL CHANGES'
                
                print 'digipal: %s ' % (status,)
                
                os.chdir(dir)
                
                # HG          
                system('hg sum', '', False, '', out)
                
                branch = re.sub(ur'(?musi)^.*branch:\s(\S+).*$', ur'\1', out['output'])
                parent = re.sub(ur'(?musi)^.*parent:\s(\S+).*$', ur'\1', out['output'])
                modified = re.sub(ur'(?musi)^.*commit:\s(\S+)\smodified.*$', ur'\1', out['output'])
                has_local_change = (len(modified) != len(out['output']))                  

                status = '%s, %s' % (branch, parent)
                if has_local_change:
                    status += ' (%s)' % 'LOCAL CHANGES'
                
                print 'digipal_django: %s ' % (status,)
            finally:
                os.chdir(dir)          
        
        if command == 'hgsub':
            known_command = True
            
            try:
                os.chdir('digipal')
                output_data = {}
                system('git log', 'Author:', True, 'Git Error', output_data)
                commits = re.findall(ur'commit (\w+)', output_data['output'])
                if commits:
                    last_commit = commits[0]
                    os.chdir(dir)
                    f = open('.hgsubstate', 'r')
                    content = f.read()
                    f.close()                    
                    # Udpate the git commit number in .hgsubstate 
                    # a81d78f70fd36c6eeb761e877ca783d7e4aae7ac digipal
                    # => LAST_GIT_COMMIT  digipal
                    content = re.sub(ur'\w+(\s+digipal)', ur'%s\1' % last_commit, content)
                    f = open('.hgsubstate', 'w')
                    f.write(content)
                    f.close()
            finally:
                os.chdir(dir)
        
        if command == 'diff':
            known_command = True
            try:
                print '> Diff main'
                run_shell_command(['hg', 'diff'])

                print '> Diff digipal'
                os.chdir('digipal')
                run_shell_command(['git', 'diff'])
                
                print '> Diff iipimage'
                os.chdir(dir)
                os.chdir('iipimage')
                run_shell_command(['git', 'diff'])
                
            finally:
                os.chdir(dir)
            
        if command == 'cs':
            known_command = True
            print '> Collect Static'
            system('python manage.py collectstatic --noinput')

        if command == 'pull':
            known_command = True
            try:
                has_sudo = get_terminal_username() == 'gnoel'
                print '> check configuration (symlinks, repo branches, etc.)'
                if not os.path.exists('iipimage') and os.path.exists('django-iipimage'):
                    if os.name == 'nt':
                        system('junction iipimage django-iipimage\iipimage')
                    else:
                        system('ln -s django-iipimage/iipimage iipimage')
                
                validation_git = r'(?i)error:'
                print '> Pull digipal'
                os.chdir('digipal')
                git_status_info = {}
                system('git status', r'(?i)on branch ('+get_allowed_branch_names_as_str()+')', True, 'Digipal should be on branch master. Try \'cd digipal; git checkout master\' to fix the issue.', git_status_info)
                branch_name = re.sub(ur'(?musi)On branch\s+(\S+).*', ur'\1', git_status_info['output'])
                
                system('git pull', validation_git)
                os.chdir(dir)
                
                print '> Pull iipimage'
                os.chdir('django-iipimage')
                system('git status', r'(?i)on branch ('+get_allowed_branch_names_as_str()+')', True, 'Digipal should be on branch master. Try \'cd digipal; git checkout master\' to fix the issue.')
                system('git pull', validation_git)
                os.chdir(dir)
                
                print '> Pull main'
                validation_hg = r'(?i)error:|abort:'
                system('hg pull', validation_hg)
                # This would cause and 'abort: uncommitted local changes'
                # in the frequent case where .hgsubstate is not up to date.
                #system('hg update -c', validation_hg)
                if os.name != 'nt':
                    # we always respond 'r' to the question:
                    # subrepository sources for digipal differ (in checked out version)
                    # use (l)ocal source (e0fc331) or (r)emote source (69a5d41)?
                    system('echo r | hg update', validation_hg)
                else:
                    system('hg update', validation_hg)

                if os.name != 'nt':
                    print '> fix permissions'
                    if has_sudo: print '\t(with sudo)'
                    sudo = ''
                    if has_sudo and not options.automatic: sudo = 'sudo '
                    system('%shown -R :digipal *' % sudo)
                    system('%shmod -R ug+rw *' % sudo)
                
                print '> South migrations'
                system('python manage.py migrate --noinput', r'(?i)!|exception|error')

                print '> Collect Static'
                system('python manage.py collectstatic --noinput')

                print '> Validate'
                system('python manage.py validate', r'0 errors found', True)
                                            
                print '> Update build info'
                system('python manage.py dpdb setbuild --branch "%s"' % branch_name)

                if os.name != 'nt':
                    print '> Touch WSGI'
                    run_shell_command(['touch', '%s/wsgi.py' % get_hg_folder_name()])

            except ExecutionError as e:
                email = options.email
                if email:
                    server_name = 'HOSTNAME'
                    send_email(email, e.title + '\n\n' + e.message, 'Pull Script ERROR on %s' % server_name)
                    print 'email sent to %s ' % email
                print e.message
                print e.title

            finally:
                os.chdir(dir)

    if not known_command:
        show_help()

def get_terminal_username():
    # not working on all systems...
    # see http://mail.python.org/pipermail/python-bugs-list/2002-July/012691.html
    ##ret = os.getlogin()
    ret = 'windows'
    try:
        import pwd
        ret = pwd.getpwuid(os.geteuid())[0]
    except:
        pass
    return ret

def read_file(file_path): 
    ret = ''
    try: 
        text_file = open(file_path, 'r')
        ret = text_file.read()
        text_file.close()
    except Exception, e:
        pass
    return ret

def system(command, validity_pattern='', pattern_must_be_found=False, error_message='', output_data=None):
    output = ''
    is_valid = True
    
    val_file = 'repo.tmp'
    if os.name != 'nt':
        os.system('%s > %s 2>&1' % (command, val_file))
    else:
        os.system('%s > %s 2>&1' % (command, val_file))
    output = read_file(val_file)
    if os.path.exists(val_file): os.unlink(val_file)
    
    if validity_pattern:
        pattern_found = re.search(validity_pattern, output) is not None 
        is_valid = (pattern_found == pattern_must_be_found)
        
    if output_data is not None:
        output_data['output'] = output
        
    if not is_valid:
        raise ExecutionError('%s - ERROR DURING EXECUTION of "%s"' % (error_message, command), output)
    
    return is_valid 

def run_shell_command(command, sudo=False):
    ret = True
    
    if sudo:
        command.insert(0, 'sudo')
    
    try:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        
        while True:
            out = process.stdout.read(1)
            if out == '' and process.poll() != None:
                break
            if out != '':
                sys.stdout.write(out)
                sys.stdout.flush()        
        #subprocess.check_output(command, stdin=subprocess.STD_INPUT_HANDLE, stdout=subprocess.STD_OUTPUT_HANDLE)
    #except subprocess.CalledProcessError, e:
    except Exception, e:
        #os.remove(input_path)
        raise Exception('Error executing command: %s (%s)' % (e, command))
        ret = False
    
    return ret

def send_email(ato, amsg, asubject, afrom='noreply@digipal.eu'):
    import smtplib
    
    # Import the email modules we'll need
    from email.mime.text import MIMEText
    
    # Open a plain text file for reading.  For this example, assume that
    # the text file contains only ASCII characters.
    # Create a text/plain message
    msg = MIMEText(amsg)
    
    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = asubject
    msg['From'] = afrom
    msg['To'] = ato
    
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(msg['From'], msg['To'].split(', '), msg.as_string())
    s.quit()           
    
process_commands()
