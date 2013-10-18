from django.conf import settings
import urllib2

def fix_sequences(db_alias, silent=False):
    ret = 0
                
    from django.db import connections
    db_name = settings.DATABASES[db_alias]['NAME']
    connection = connections[db_alias]
    cursor = connection.cursor()

    select_seq_info = ur'''
        select table_name, column_name
        from information_schema.columns
        where table_catalog = %s
        and column_default like %s
        order by table_name
        '''
    
    cur = sqlSelect(connection, select_seq_info, [db_name, ur'nextval%'])
    while True:
        rec = cur.fetchone()
        if not rec: break
        params = {'table_name': rec[0], 'seq_field': rec[1]}
        if not silent:
            print '%s.%s' % (params['table_name'], params['seq_field'])
        cmd = "select setval('%(table_name)s_%(seq_field)s_seq', (select max(%(seq_field)s) from %(table_name)s) )" % params
        cursor.execute(cmd)
        ret += 1
    cur.close()
    cursor.close()
    
    return ret

def sqlWrite(wrapper, command, arguments=[], dry_run=False):
    if not dry_run:
        cur = wrapper.cursor()

        #print command
        cur.execute(command, arguments)
        #wrapper.commit()
        cur.close()

def sqlSelect(wrapper, command, arguments=[]):
    ''' return a cursor,
        caller need to call .close() on the returned cursor 
    '''
    cur = wrapper.cursor()
    cur.execute(command, arguments)
    
    return cur

def sqlSelectMaxDate(con, table, field):
    ret = None
    cur = sqlSelect(con, 'select max(%s) from %s' % (field, table))
    rec = cur.fetchone()
    if rec and rec[0]:
        ret = rec[0]
    cur.close()
    
    return ret

def sqlSelectCount(con, table):
    ret = 0
    cur = sqlSelect(con, 'select count(*) from %s' % table)
    rec = cur.fetchone()
    ret = rec[0]
    cur.close()
    
    return ret

def sqlDeleteAll(con, table, dry_run=False):
    ret = True
    
    from django.db import IntegrityError

    try:
        sqlWrite(con, 'delete from %s' % table, [], dry_run)
    except IntegrityError, e:
        print e
        ret = False

    return ret

def dropTable(con, table_name, dry_run=False):
    if dry_run: return

    sqlWrite(con, 'DROP TABLE %s CASCADE' % table_name, [], dry_run)

def readFile(filepath):
    import codecs
    f = codecs.open(filepath, 'r', "utf-8")
    ret = f.read()
    f.close()
    
    return ret

class Logger(object):
    
    FATAL   = 0
    WARNING = 1
    INFO    = 2
    DEBUG   = 3
    
    def __init__(self, log_level=None):
        self.setLogLevel(log_level)
        self.resetWarning()
                        
    def setLogLevel(self, log_level=None):
        self.log_level = log_level
        if self.log_level is None: self.log_level = Logger.DEBUG
        
    def resetWarning(self):
        self.warning_count = 0

    def hasWarning(self):
        return self.warning_count

    def log(self, message, log_level=3, indent=0):
        if log_level < Logger.INFO:
            self.warning_count += 1
        
        if log_level <= self.log_level:
            prefixes = ['ERROR: ', 'WARNING: ', '', ''] 
            from datetime import datetime
            timestamp = datetime.now().strftime("%y-%m-%d %H:%M:%S")
            try:
                indent_str = '    ' * indent
                print (u'[%s] %s%s%s' % (timestamp, indent_str, prefixes[log_level], message)).encode('utf-8')
            except UnicodeEncodeError:
                print '???'

def write_file(file_name, data):
    f = open(file_name, 'wb')
    f.write(data)
    f.close()
        
def wget(url):
    ret = None
    try:
        response = urllib2.urlopen(url)
        ret = response.read()
    except Exception, e:
        ret = None
    return ret

def get_simple_str(str):
    import re
    return re.sub(ur'\W+', '_', str.strip().lower())

def is_int(str):
    try:
        int(str)
    except ValueError:
        return False
    return True
