# How to make a backup of your framework content:
# got to the terminal (On Kitematic, click Exec when DigiPal/Archetype is running)
# then type/paste these lines (press ENTER/RETURN key at then end of each):
# apt-get install -y wget
# wget -qO zip_digipal_project.py http://bit.ly/2xERjk7 && python zip_digipal_project.py
# exit
#
# TODO:
# Don't leave backup in static (or use random number for folder name)
# use plain zip

import os
import re
import sys
import glob
from subprocess import check_output


def run_cmd(command):
    res = check_output(command, shell=True)
    return res


class ProjectZipper(object):

    def import_settings(self):
        manage_path = 'manage.py'
        found = 0
        for i in range(0, 5):
            found = os.path.exists(manage_path)
            if found:
                break
            manage_path = os.path.join('..', manage_path)

        if not found:
            print('WARNING: could not find manage.py in this folder or parents')
            return

        print 'manage.py: ' + manage_path
        dirname = os.path.dirname(manage_path)
        if dirname:
            os.chdir(dirname)

        settings_module = run_cmd(
            'grep "DJANGO_SETTINGS_MODULE" ' + manage_path)
        eval(re.sub(r'(?musi)^\s+', '', settings_module))
        settings_module = os.environ['DJANGO_SETTINGS_MODULE']

        print 'setting: ' + settings_module
        from importlib import import_module
        sys.path.append('.')
        self.settings = import_module(settings_module)

        # old style: digipal app is also the django project
        self.is_digipal_app_the_project = os.path.exists(
            os.path.join(self.settings.PROJECT_ROOT, 'repo.py')
        )

    def get_dst_path(self, part=None):
        ret = os.path.join(self.settings.STATIC_ROOT)
        if part:
            ret = os.path.join(ret, part)
        return ret

    def dump_database(self):
        settings = self.settings
        sql_filename = 'archetype.sql'
        sql_path = self.get_dst_path(sql_filename)

        DB = settings.DATABASES['default']

        host = DB['HOST']
        port = DB['PORT']
        if port:
            port = '-p ' + port
        if host:
            host = '-h ' + host
        username = DB['USER']
        dbname = DB['NAME']
        password = DB['PASSWORD']
        os.environ['PGPASSWORD'] = password
        # removed --if-exists because it requires pg_dump 9.4+ > version installed on older archetype-docker
        # without --if-exists the restoration will show harmless warnings
        command = 'pg_dump -c -U %s %s --exclude-table-data=digipal_text_textcontentxmlcopy %s %s > "%s"' % (
            username, dbname, host, port, sql_path)
        res = run_cmd(command)

        self.add_path_to_tar(sql_path)

        run_cmd('rm -f %s' % sql_path)

        print 'Database saved into %s' % sql_path
        # print 'Download it at %s' % os.path.join(settings.STATIC_URL,
        # sql_filename)

    def get_tar_path(self):
        return os.path.join(self.get_dst_path(), 'archetype.tar')

    def add_path_to_tar(self, paths, transforms=None):
        '''<paths>: a list of file apths to be added to the tar file.
        <paths> can contain wildcards.
        If <transform> is specified, it is a list of pairs of
        filename replacement expressions.
        E.g. [['myfile', 'yourfile']]
        Note that replacement applies to any part of the filenames.
        '''

        if hasattr(paths, 'replace'):
            # convert string input to list
            paths = [paths]

        paths_to_tar = []
        for path in paths:
            apaths = glob.glob(path.rstrip('/'))
            for apath in apaths:
                if not os.path.exists(apath):
                    print('WARNING: path "%s" not found' % (apath))
                    continue

                paths_to_tar.append(apath)

        if paths_to_tar:
            if hasattr(transforms, 'replace'):
                # convert string input to list
                transforms = [[os.path.basename(paths_to_tar[0]), transforms]]

            transforms_option = ' '.join([
                "--transform='flags=r;s|%s|%s|'" % (t[0], t[1])
                for t in (transforms or [])
            ])
            # Note: -h will make tar crash in some containers
            run_cmd('tar %s --append -f %s -C %s %s' % (
                transforms_option,
                self.get_tar_path(),
                os.path.dirname(paths_to_tar[0]),
                ' '.join([os.path.basename(p) for p in paths_to_tar])
            ))

    def create_tar(self):
        run_cmd('tar -cf %s --files-from /dev/null' % self.get_tar_path())

    def save_pid(self, clear=False):
        pid = 0 if clear else os.getpid()
        with open(os.path.join(self.get_dst_path(), '.packager.pid'), 'wt') as fh:
            fh.write(str(pid))

    def zip_project(self):
        self.import_settings()

        self.save_pid()

        self.create_tar()

        # database
        self.dump_database()

        # customisations
        self.add_path_to_tar(
            os.path.join(self.settings.PROJECT_ROOT, 'customisations')
        )
        # templates
        if not self.is_digipal_app_the_project:
            self.add_path_to_tar(os.path.join(
                self.settings.PROJECT_ROOT, 'templates')
            )
        # media
        self.add_path_to_tar(self.settings.MEDIA_ROOT, 'media')
        # images
        self.add_path_to_tar(self.settings.IMAGE_SERVER_ROOT, 'images')

        # config files
        files_to_tar = ['*.py']
        # We make space for a special settings.py that enables dockers config
        tar_transforms = [['^settings.py$', 'settings.py.bk']]
        if self.is_digipal_app_the_project:
            # files_to_tar = ['urls.py', 'local_settings.py']
            tar_transforms = None

        self.add_path_to_tar(
            [
                os.path.join(self.settings.PROJECT_ROOT, p)
                for p
                in files_to_tar
            ],
            tar_transforms
        )

        # Now zip it all
        run_cmd('gzip -f3 %s' % self.get_tar_path())

        print 'Download your backup at: %s' % (os.path.join(self.settings.STATIC_URL, 'archetype.tar.gz'), )
        # os.system('chmod ugo+rw %s.tar' % self.get_dst_path())

        self.save_pid(True)


zipper = ProjectZipper()
zipper.zip_project()
