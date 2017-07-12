#!/usr/bin/env python
'''
Repository management tool.

Please try to keep the code cross-OS compatible: Windows and Linux.
'''
from optparse import OptionParser
import os
import sys
import re
import subprocess

import repo_cfg as config


def get_config(varname='', default=''):
    return getattr(config, varname, default)


class ExecutionError(Exception):

    def __init__(self, title, message):
        self.title = title
        self.message = message


def show_help():
    print '''Usage: python %s [OPTIONS] COMMAND

Commands:

  pull
    Upgrade code from repositories
    Database upgrade
    Django validation
    Fixes file permissions
    Collect static files
    Reload site
    
  perms
    Fix file permissions

  diff
    Lists the difference across all repos

  cs
    Collectstatic
    
  st
    Show repos status
    
  nc
    No cache; remove all cached data

  g [...]
    from the git folder, executes git [...]

Options:

  -a --automatic
     no interaction or user input required

  -e --email=EMAIL_ADDRESS
     send error message to EMAIL_ADDRESS

  --nohg
     pull command ignores hg repo
     
''' % os.path.basename(__file__)
    exit


def get_allowed_branch_names():
    return ['master', 'staging', 'ref2014']


def get_allowed_branch_names_as_str():
    return '|'.join(get_allowed_branch_names())


def get_hg_folder_name():
    ret = ''
    for root, dirs, files in os.walk('.'):
        if 'local_settings.py' in files:
            ret = root
            break
    return ret


def get_github_dir():
    github_dir = ''
    for ghpath in ['digipal_github/digipal/digipal', 'digipal_github/digipal']:
        if os.path.exists(ghpath + '/repo_cfg.py'):
            github_dir = ghpath
            break
    if not github_dir:
        github_dir = os.path.dirname(config.__file__)
    return github_dir


def process_commands():
    original_dir = os.getcwd()

    #parent_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
    # os.chdir(parent_dir)

    try:
        process_commands_main_dir()
    finally:
        os.chdir(original_dir)


def process_commands_main_dir():
    parser = OptionParser()
    parser.add_option("-a", "--automatic",
                      action="store_true", dest="automatic", default=False,
                      help="no input necessary")
    parser.add_option("-e", "--email",
                      action="store", dest="email", default='',
                      help="email to send errors to")
    parser.add_option("-m", "--mmmm",
                      action="store", dest="mmmm", default='',
                      help="Just for git -am")
    parser.add_option("--nohg",
                      action="store_true", dest="nohg", default=False,
                      help="skip hg pull")

    (options, args) = parser.parse_args()

    known_command = False

    if len(args):
        command = args[0]
        original_dir = os.getcwd()

        github_dir = get_github_dir()
        project_folder = get_hg_folder_name()

        username = get_terminal_username()

        print 'Project folder: %s' % project_folder
        print 'GitHub folder: %s' % github_dir

        if command == 'nc':
            known_command = True
            dirs = ['django_cache', 'static/CACHE']
            for adir in dirs:
                dir = os.path.join(project_folder, adir)
                print 'Empty %s' % dir
                if not os.path.isdir(dir):
                    print 'WARNING: path not found.'
                else:
                    # TODO: windows command
                    cmd = 'sudo rm -r %s/*' % dir
                    res = system(cmd)
            print 'done'

        if command == 'perms':
            known_command = True
            fix_permissions(username, project_folder, options)

        if command == 'g':
            known_command = True
            argms = sys.argv[2:]
            print repr(argms)
            os.chdir(github_dir)

            for pair in [['s', 'status'], ['p', 'pull'], ['l', 'log']]:
                if argms[0] == pair[0]:
                    argms[0] = pair[1]
                    break

            #os.system('git %s' % (' '.join(argms)))
            import subprocess
            argms.insert(0, 'git')
            subprocess.call(argms, shell=False)

        if command == 'st':
            known_command = True

            try:
                out = {}

                # GIT
                # print globals()
                os.chdir(github_dir)
                system('git status', '', False, '', out)

                branch = re.sub(ur'(?musi)^.*on branch (\S+).*$',
                                ur'\1', out['output'])
                has_local_change = (out['output'].find('modified:') > -1)

                status = branch
                if has_local_change:
                    status += ' (%s)' % 'LOCAL CHANGES'

                print 'digipal: %s ' % (status,)

                if not config.SELF_CONTAINED:
                    os.chdir(original_dir)

                    # HG
                    system('hg sum', '', False, '', out)

                    branch = re.sub(
                        ur'(?musi)^.*branch:\s(\S+).*$', ur'\1', out['output'])
                    parent = re.sub(
                        ur'(?musi)^.*parent:\s(\S+).*$', ur'\1', out['output'])
                    modified = re.sub(
                        ur'(?musi)^.*commit:\s(\S+)\smodified.*$', ur'\1', out['output'])
                    has_local_change = (len(modified) != len(out['output']))

                    status = '%s, %s' % (branch, parent)
                    if has_local_change:
                        status += ' (%s)' % 'LOCAL CHANGES'

                    print 'Mercurial: %s ' % (status, )
            finally:
                os.chdir(original_dir)

        if command == 'diff':
            known_command = True
            try:
                print '> Diff main'
                run_shell_command(['hg', 'diff'])

                print '> Diff digipal'
                os.chdir('digipal')
                run_shell_command(['git', 'diff'])

#                 print '> Diff iipimage'
#                 os.chdir(original_dir)
#                 os.chdir('iipimage')
#                 run_shell_command(['git', 'diff'])

            finally:
                os.chdir(original_dir)

        if command == 'cs':
            known_command = True
            print '> Collect Static'
            system('python manage.py collectstatic --noinput')

        if command == 'pull':
            known_command = True
            try:
                print 'Main app folder: %s' % project_folder

                print '> check configuration (symlinks, repo branches, etc.)'
#                 if not os.path.exists('iipimage') and os.path.exists('django-iipimage'):
#                     if os.name == 'nt':
#                         system('junction iipimage django-iipimage\iipimage')
#                     else:
#                         system('ln -s django-iipimage/iipimage iipimage')

                for path in ('iipimage', 'django-iipimage'):
                    if os.path.exists(path):
                        print '> remove %s' % path
                        if os.name == 'nt':
                            system('del /F /S /Q %s' % path)
                            system('rmdir /S /Q %s' % path)
                        else:
                            system('rm -r %s' % path)

                validation_git = r'(?i)error:'
                print '> Pull digipal (%s)' % github_dir
                os.chdir(github_dir)
                git_status_info = {}
                #system('git status', r'(?i)on branch ('+get_allowed_branch_names_as_str()+')', True, 'Digipal should be on branch master. Try \'cd digipal_github; git checkout master\' to fix the issue.', git_status_info)
                system('git status', output_data=git_status_info)
                branch_name = re.sub(
                    ur'(?musi)On branch\s+(\S+).*', ur'\1', git_status_info['output'])

                system('git pull', validation_git)
                os.chdir(original_dir)

                if not config.SELF_CONTAINED and not options.nohg:
                    print '> Pull main'
                    validation_hg = r'(?i)error:|abort:'
                    system('hg pull', validation_hg)
                    # This would cause and 'abort: uncommitted local changes'
                    # in the frequent case where .hgsubstate is not up to date.
                    #system('hg update -c', validation_hg)
                    if os.name != 'nt':
                        # we always respond 'r' to the question:
                        # subrepository sources for digipal differ (in checked out version)
                        # use (l)ocal source (e0fc331) or (r)emote source
                        # (69a5d41)?
                        system('echo r | hg update', validation_hg)
                    else:
                        system('hg update', validation_hg)

                # FIX PERMISSIONS
                fix_permissions(username, project_folder, options)

                print '> South migrations'
                system('python manage.py migrate --noinput',
                       r'(?i)!|exception|error')

                if not get_config('DJANGO_WEB_SERVER'):
                    print '> Collect Static'
                    system('python manage.py collectstatic --noinput')
                else:
                    print '> Collect Static (skipped: django webserver)'

                print '> Validate'
                system('python manage.py check', r'no issues', True)

                print '> Update build info'
                system('python manage.py dpdb setbuild --branch "%s"' %
                       branch_name)

                if os.name != 'nt':
                    print '> Touch WSGI'
                    run_shell_command(['touch', '%s/wsgi.py' % project_folder])

            except ExecutionError as e:
                email = options.email
                if email:
                    server_name = 'HOSTNAME'
                    send_email(email, e.title + '\n\n' + e.message,
                               'Pull Script ERROR on %s' % server_name)
                    print 'email sent to %s ' % email
                print e.message
                print e.title

            finally:
                os.chdir(original_dir)

    if not known_command:
        show_help()


def fix_permissions(username, project_folder, options):
    if os.name == 'nt':
        return

    sudo_users = get_config('SUDO_USERS', ['gnoel', 'jeff'])
    has_sudo = not options.automatic and username in sudo_users

    sudo = with_sudo = ''
    if has_sudo:
        with_sudo = '(with sudo)'
        sudo = 'sudo '
    print '> fix permissions %s' % with_sudo

    web_service_user = 'www-data'
    puller = username
    if get_config('DJANGO_WEB_SERVER', False):
        web_service_user = username

    # ALL files belong to PROJECT_GROUP
    system('%schgrp %s -R .' % (sudo, config.PROJECT_GROUP))

    # ALL files belong to www-data or current user
    if has_sudo:
        system('%schown %s -R .' % (sudo, web_service_user))

    # -r- xrw x---
    default_perms = 570
    # eclipse need owner write
    # builder need to modify code
    if get_config('ECLIPSE_EDITABLE', False) or \
       get_config('BUILT_BY_WWW_DATA', False):
        # -rw xrw x---
        default_perms = 770
        puller = web_service_user
    system('%schmod %s -R .' % (sudo, default_perms))

    # some files can be written by web service
    dirs = [d for d in ('%(p)s/static/CACHE;%(p)s/django_cache;%(p)s/search;%(p)s/logs;%(p)s/media/uploads;.hg' %
                        {'p': project_folder}).split(';') if os.path.exists(d)]
    system('%schmod 770 -R %s' % (sudo, ' '.join(dirs)))

    # prevent user from rewriting the indexes if they are managed by web
    # service
    if not get_config('DJANGO_WEB_SERVER', False):
        dirs = [d for d in ('%(p)s/search' %
                            {'p': project_folder}).split(';') if os.path.exists(d)]
        system('%schmod 750 -R %s' % (sudo, ' '.join(dirs)))

    if has_sudo:
        # .hg must be owned by the user pulling otherwise mercurial
        # complains.

        system('%schown %s -R .hg' % (sudo, puller))

    if 0:
        # See MOA-197
        if username == 'www-data' or username == config.PROJECT_GROUP:
            # -rw xrw x---
            system('%schown :%s -R .' % (sudo, config.PROJECT_GROUP))
            system('%schmod 770 -R .' % sudo)
            #system('%schgrp -R %s .' % (sudo, config.PROJECT_GROUP))
        else:
            if has_sudo:
                # all files belong to www-data:PROJECT_GROUP
                system('%schown www-data:%s -R .' %
                       (sudo, config.PROJECT_GROUP))

                # Except repos metadata
                # (to avoid repos complaining about wrong owner)
                ##system('%schown %s:%s -R .hg' % (sudo, username, config.PROJECT_GROUP))
                ##system('%schown %s:%s -R %s/.git' % (sudo, username, config.PROJECT_GROUP, github_dir))

            # -r- xrw x---
            default_perms = 570
            if get_config('ECLIPSE_EDITABLE', False) or get_config('BUILT_BY_WWW_DATA', False):
                default_perms = 770
            system('%schmod %s -R .' % (sudo, default_perms))
            # -rw xrw x---
            dirs = [d for d in ('%(p)s/static/CACHE;%(p)s/django_cache;%(p)s/search;%(p)s/logs;%(p)s/media/uploads;.hg' %
                                {'p': project_folder}).split(';') if os.path.exists(d)]
            system('%schmod 770 -R %s' % (sudo, ' '.join(dirs)))
            dirs = [d for d in ('%(p)s/static/CACHE;%(p)s/django_cache;%(p)s/search;%(p)s/logs;%(p)s/media/uploads;.hg' %
                                {'p': project_folder}).split(';') if os.path.exists(d)]
            system('%schmod u-w -R %s' % (sudo, ' '.join(dirs)))

    # we do this because the cron job to reindex the content
    # recreate the dirs with owner = gnoel:ddh-research
    #system('%schmod o+r -R %s/search' % (sudo, project_folder))
    #system('%schmod o+x -R %s/search/*' % (sudo, project_folder))


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
    if os.path.exists(val_file):
        os.unlink(val_file)

    if validity_pattern:
        pattern_found = re.search(validity_pattern, output) is not None
        is_valid = (pattern_found == pattern_must_be_found)

    if output_data is not None:
        output_data['output'] = output

    if not is_valid:
        raise ExecutionError('%s - ERROR DURING EXECUTION of "%s"' %
                             (error_message, command), output)

    return is_valid


def run_shell_command(command, sudo=False, aout=None):
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
    # except subprocess.CalledProcessError, e:
    except Exception, e:
        # os.remove(input_path)
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
