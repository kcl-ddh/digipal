from django.conf import settings

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
