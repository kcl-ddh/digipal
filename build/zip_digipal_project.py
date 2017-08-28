import os
import re
import sys
from subprocess import call, check_output


def run_cmd(command):
    res = check_output(command, shell=True)
    return res


manage_path = run_cmd('find .. -name manage.py | tail -n 1')
manage_path = manage_path.strip('\n')

print 'manage.py: ' + manage_path
os.chdir(os.path.dirname(manage_path))

settings_module = run_cmd('grep "DJANGO_SETTINGS_MODULE" ' + manage_path)
eval(re.sub(r'(?musi)^\s+', '', settings_module))
settings_module = os.environ['DJANGO_SETTINGS_MODULE']

print 'setting: ' + settings_module
from importlib import import_module
sys.path.append('.')
settings = import_module(settings_module)

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
command = 'pg_dump -U %s %s -c %s %s > archetype.sql' % (
    username, dbname, host, port)
os.system(command)
