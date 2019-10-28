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
from subprocess import check_output


def run_cmd(command):
    res = check_output(command, shell=True)
    return res


class ProjectZipper(object):

    def import_settings(self):
        manage_path = run_cmd('find .. -name manage.py | tail -n 1')
        manage_path = manage_path.strip('\n')

        print 'manage.py: ' + manage_path
        os.chdir(os.path.dirname(manage_path))

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
            os.path.join(self.settings.PROJECT_ROOT, 'repo.py'))

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
        print command
        os.system(command)

        self.add_path_to_tar(sql_path)

        run_cmd('rm -f %s' % sql_path)

        print 'Database saved into %s' % sql_path
        # print 'Download it at %s' % os.path.join(settings.STATIC_URL,
        # sql_filename)

    def get_tar_path(self):
        return os.path.join(self.get_dst_path(), 'archetype.tar')

    def add_path_to_tar(self, path, new_name=None):
        path = path.rstrip('/')

        if os.path.exists(path):
            new_path = None
            if new_name and os.path.basename(path) != new_name:
                new_path = os.path.join('/tmp', new_name)
                run_cmd('cp -rfL %s %s' % (path, new_path))
                path = new_path

            # Note: -h wil make tar crash in some containers
            run_cmd('tar --append -f %s -C %s %s' %
                    (self.get_tar_path(), os.path.dirname(path), os.path.basename(path)))

            if new_path:
                run_cmd('rm -rf %s' % new_path)

    def create_tar(self):
        run_cmd('tar -cf %s --files-from /dev/null' % self.get_tar_path())

    def zip_project(self):
        self.import_settings()

        self.create_tar()

        # database
        self.dump_database()

        # customisations
        self.add_path_to_tar(os.path.join(
            self.settings.PROJECT_ROOT, 'customisations'))
        # templates
        if not self.is_digipal_app_the_project:
            self.add_path_to_tar(os.path.join(
                self.settings.PROJECT_ROOT, 'templates'))
        # media
        self.add_path_to_tar(self.settings.MEDIA_ROOT, 'media')
        # images
        self.add_path_to_tar(self.settings.IMAGE_SERVER_ROOT, 'images')

        # TODO: local_settings.py, settings.py and urls.py
        if not self.is_digipal_app_the_project:
            self.add_path_to_tar(os.path.join(
                self.settings.PROJECT_ROOT, 'settings.py'), 'settings.py.bk')
        self.add_path_to_tar(os.path.join(
            self.settings.PROJECT_ROOT, 'local_settings.py'), 'local_settings.py')
        self.add_path_to_tar(os.path.join(
            self.settings.PROJECT_ROOT, 'urls.py'), 'urls.py')

        # Now zip it all
        run_cmd('gzip -f1 %s' % self.get_tar_path())

        print 'Download your backup at: %s' % (os.path.join(self.settings.STATIC_URL, 'archetype.tar.gz'), )
#                                                         ))
        # os.system('chmod ugo+rw %s.tar' % self.get_dst_path())


zipper = ProjectZipper()
zipper.zip_project()
