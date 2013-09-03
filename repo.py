#!/usr/bin/env python
from optparse import OptionParser
import os, sys, re
import subprocess

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
    ''' % os.path.basename(__file__)
    exit

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
    parser.add_option("-f", "--file", dest="filename",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")
    
    (options, args) = parser.parse_args()

    known_command = False
    
    if len(args):
        command = args[0]
        dir = os.getcwd()
        
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
                system('git status', r'(?i)on branch (master|staging)', True, 'Digipal should be on branch master. Try \'cd digipal; git checkout master\' to fix the issue.')
                system('git pull', validation_git)
                os.chdir(dir)
                
                print '> Pull iipimage'
                os.chdir('django-iipimage')
                system('git status', r'(?i)on branch (master|staging)', True, 'Digipal should be on branch master. Try \'cd digipal; git checkout master\' to fix the issue.')
                system('git pull', validation_git)
                os.chdir(dir)
                
                print '> Pull main'
                validation_hg = r'(?i)error:|abort:'
                system('hg pull', validation_hg)
                system('hg update -c', validation_hg)

                if os.name != 'nt':
                    print '> fix permissions'
                    if has_sudo: print '\t(with sudo)'
                    sudo = ''
                    if has_sudo: sudo = 'sudo '
                    system('%shown -R :digipal *' % sudo)
                    system('%shmod -R ug+rw *' % sudo)
                
                print '> South migrations'
                system('python manage.py migrate --noinput', r'(?i)!|exception|error')

                print '> Collect Static'
                system('python manage.py collectstatic --noinput')

                print '> Validate'
                system('python manage.py validate', r'0 errors found', True)
                                            
                if os.name != 'nt':
                    print '> Touch WSGI'
                    run_shell_command(['touch', '%s/wsgi.py' % get_hg_folder_name()])

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

def system(command, validity_pattern='', pattern_must_be_found=False, error_message=''):
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
        
    if not is_valid:
        print output
        print 'ERROR DURING EXECUTION of (%s, see above)' % command
        if error_message:
            print error_message
        exit()
    
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

process_commands()
