from mezzanine.conf import settings
from digipal import utils as dputils
import urllib2


def get_stats_from_xml_string(xml_string, text_label='', stats=None):
    #     print 'Count - Tag'
    #     print

    els = {}
    if stats is not None:
        els = stats

    import regex as re

#     elements = re.findall(ur'<(\w+)', xml_string)
#     for el in set(elements):
#         print '%8d %s' % (elements.count(el), el)

#     print
#     print 'Unique tag-attributes'
#     print
    elements = re.findall(ur'<([^/!?>][^>]*)>', xml_string)
    for el in elements:
        el = el.strip()
        if el not in els:
            els[el] = {'text': text_label, 'count': 1}
        else:
            els[el]['count'] += 1

    return els

#     for el in sorted(els):
#         print el


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
        if not rec:
            break
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

        # print command
        cur.execute(command, arguments)
        # wrapper.commit()
        cur.close()
        cur = None


def sqlSelect(wrapper, command, arguments=[]):
    ''' return a cursor,
        caller need to call .close() on the returned cursor
    '''
    cur = wrapper.cursor()
    cur.execute(command, arguments)

    return cur


def fetch_all_dic(cursor, key_field_name=None):
    ret = {}
    desc = cursor.description
    if key_field_name is None:
        key_field_name = desc[0][0]
    for row in cursor.fetchall():
        row = dict(zip([col[0] for col in desc], row))
        ret[row[key_field_name]] = row
    cursor.close()
    return ret


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
    if dry_run:
        return

    sqlWrite(con, 'DROP TABLE %s CASCADE' % table_name, [], dry_run)


def readFile(filepath):
    from digipal.utils import read_file
    return read_file(filepath)


class Logger(object):

    FATAL = 0
    WARNING = 1
    INFO = 2
    DEBUG = 3

    def __init__(self, log_level=None):
        self.setLogLevel(log_level)
        self.resetWarning()

    def setLogLevel(self, log_level=None):
        self.log_level = log_level
        if self.log_level is None:
            self.log_level = Logger.DEBUG

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
                print (u'[%s] %s%s%s' % (timestamp, indent_str,
                                         prefixes[log_level], message)).encode('utf-8')
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


def get_obj_label(obj):
    return '%s #%d: %s' % (obj._meta.object_name, obj.id, obj)


def web_fetch(url, username=None, password=None, sessionid=None, noredirect=False):
    ret = {'error': None, 'response': None,
           'status': 0, 'reason': None, 'body': None}

    import urlparse
    parts = urlparse.urlsplit(url)

    import httplib
    from base64 import b64encode
    port = parts.port
    if parts.scheme == 'https':
        port = 443
        conn = httplib.HTTPSConnection(parts.hostname, port)
    else:
        conn = httplib.HTTPConnection(parts.hostname, port)

    options = {}
    if username:
        userAndPass = b64encode(username + ':' + password)
        headers = {'Authorization': 'Basic %s' % userAndPass}
        options['headers'] = headers

    if sessionid:
        options['headers'] = {'Cookie': 'sessionid=%s' % sessionid}

    try:
        conn.request('GET', parts.path + '?' + parts.query, **options)

        ret['response'] = conn.getresponse()

        headers = dict(ret['response'].getheaders())
        ret['status'] = '%s' % ret['response'].status
        ret['reason'] = '%s' % ret['response'].reason
        ret['body'] = ret['response'].read()

        if not noredirect and headers.has_key('location') and headers['location'] != url:
            # follow redirect
            ret = web_fetch(headers['location'])
        conn.close()
    except StandardError, e:
        ret['error'] = e

    return ret


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def prnt(txt):
    '''A safe print function that won't generate encoding errors'''
    print txt.encode('utf8', 'ignore')


def get_bool_from_mysql(mysql_bool='-1'):
    '''Returns True/False from a mysql boolean field'''
    return mysql_bool and unicode(mysql_bool) == '-1'


class CommandMessages(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.summary = {}

    def msg(self, message, *args, **kwargs):
        category = kwargs.get('category', 'WARNING')
        message = '%s: %s' % (category, message)
        message = message.replace('%s', '{}')
        print message.format(*args)
        self.summary[message] = self.summary.get(message, 0) + 1

    def printSummary(self):
        if not self.summary:
            return
        print '=' * 40
        print 'MESSAGES SUMMARY'
        for msg, count in self.summary.iteritems():
            print count, msg
