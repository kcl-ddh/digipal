from django.core.management.base import BaseCommand, CommandError
from mezzanine.conf import settings
from os.path import isdir
import os
import shlex
import subprocess
import re
from optparse import make_option
import utils
from utils import Logger
from digipal.views.faceted_search.search_indexer import SearchIndexer
from __builtin__ import True


class Command(BaseCommand):
    help = """
Digipal search tool.

Commands:

  index
    Re-Index all the content

  info [--if=KEYWORD] [--qs=QUERY_STRING] [--limit=LIMIT] [--field=FIELD]
    Show general info and whoosh schemas
    If QUERY STRING is provided, runs a whoosh search
    e.g. info --if=graphs --qs="character:O NOT position:unspecified"
    e.g. info --if=graphs --qs=ANY
    e.g. info --if=graphs --field=position

  index_facets
    Re-Index the faceted content

  dump
    Dump indices

  search --if=KEYWORD [--user=USERNAME] [--qs=QUERY_STRING]
    Faceted Search

  clear
    Clear the faceted search cache

Options:

  --if=INDEX_NAME
                        Work only with index INDEX_NAME

  --ctf=CONTENT_TYPE_NAME
                        Work only with content type CONTENT_TYPE_NAME
                        e.g. hand

  --user=USERNAME

  --qs=QUERY_STRING

"""

    args = 'index'
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    action='store_true',
                    dest='dry-run',
                    default=False,
                    help='Dry run, don\'t change any data.'),
        make_option('--if',
                    action='store',
                    dest='index_filter',
                    default=None,
                    help='The name of the index to work with (All if unspecified)'),
        make_option('--user',
                    action='store',
                    dest='user',
                    default='',
                    help='The name of a Django user'),
        make_option('--qs',
                    action='store',
                    dest='qs',
                    default='',
                    help='A query string'),
        make_option('--limit',
                    action='store',
                    dest='limit',
                    default='',
                    help='number of hits to return'),
        make_option('--field',
                    action='store',
                    dest='field',
                    default='',
                    help='field name'),
        make_option('--ctf',
                    action='store',
                    dest='content_type_filter',
                    default=None,
                    help='The name of the content type to work with (All if unspecified)'),
    )

    def handle(self, *args, **options):
        self.logger = utils.Logger()

        self.log_level = 3

        self.options = options

        if len(args) < 1:
            raise CommandError(
                'Please provide a command. Try "python manage.py help dpsearch" for help.')
        command = args[0]

        known_command = False

        if command == 'clear':
            known_command = True
            self.clear_cache()

        if command == 'search':
            known_command = True
            self.search()

        if command == 'index':
            known_command = True
            self.index_all(options)

        if command == 'index_facets':
            known_command = True
            self.index_facets(options)
            self.clear_cache()

        if command == 'schema':
            known_command = True
            self.schema(options)

        if command == 'info':
            known_command = True
            self.info(options)

        if command == 'dump':
            known_command = True
            self.dump(options)

        if command == 'test':
            known_command = True
            self.test(options)

        if command == 'index_graph':
            known_command = True
            self.index_graph_description()

        if self.is_dry_run():
            self.log(
                'Nothing actually written (remove --dry-run option for permanent changes).', 1)

        if not known_command:
            print Command.help

    def clear_cache(self):
        from digipal.views.faceted_search import faceted_search
        cache = faceted_search.FacetedModel.get_cache()
        cache.clear()
        print 'Cache cleared'

    def dump(self, options):
        for name in self.get_requested_index_names():
            print 'Schemas - %s' % name
            dir_abs = os.path.join(settings.SEARCH_INDEX_PATH, name)

            print '\t%s' % dir_abs

            from whoosh.index import open_dir
            from whoosh.query import Every
            index = open_dir(dir_abs)

            q = Every()
            with index.searcher() as searcher:
                hits = searcher.search(q, limit=None)
                for hit in hits:
                    print ('\t%s' % repr(hit)).encode('ascii', 'ignore')

    def get_filtered_indexes(self):
        ''' returns a list of index names passed in the --if=f1,f2 command line option'''
        ret = self.options['index_filter']
        if ret:
            ret = ret.split(',')
        else:
            ret = []
        return ret

    def get_all_dirs_under_index_path(self):
        ''' returns the absolute path to all the index folders
        (optionally filtered by --if command line option)'''
        from digipal.utils import get_all_files_under
        ret = get_all_files_under(
            settings.SEARCH_INDEX_PATH, filters=self.get_filtered_indexes())
        return ret

    def info(self, options):
        for dir in self.get_all_dirs_under_index_path():
            if not os.path.isdir(dir):
                continue
            from datetime import datetime
            dir_rel = os.path.relpath(dir, settings.SEARCH_INDEX_PATH)
            print '-' * 78
            print dir_rel
            info = self.get_index_info(dir)
            print '  size  : %.2f MB' % (info['size'] / 1024.0 / 1024.0)
            print '  date  : %s' % datetime.fromtimestamp(info['date'])
            print '  docs  : %s' % info['entries']

            print '  fields:'
            for field in info['fields']:
                print '    %25s: %10s %6s %12s %12s' % (field['name'], field['type'], field['unique_values'], field['range'][0], field['range'][1])
            print '  segments:'
            for seg in info['segments']:
                print '    %25s: %s' % (seg['id'], seg['entries'])

            values = info.get('values', [])
            if values:
                print '\n  %s:' % self.options['field']
                i = 0
                for value in values:
                    print '\t', i, repr(value)
                    i += 1

            results = info.get('results', '')
            if results:
                print '\n  results:'
                print results

    def get_index_info(self, path):
        ret = {'date': 0, 'size': 0, 'fields': [],
               'entries': '?', 'segments': []}

        # basic filesystem info
        from digipal.utils import get_all_files_under
        for file in get_all_files_under(path, file_types='f'):
            ret['size'] += os.path.getsize(file)
            ret['date'] = max(ret['date'], os.path.getmtime(file))

        # whoosh info
        import whoosh
        from whoosh.index import open_dir
        index = None
        try:
            index = open_dir(path)
        except whoosh.index.EmptyIndexError:
            pass

        query = self.options['qs']
        afield = self.options['field']

        if index:
            with index.searcher() as searcher:
                ret['entries'] = searcher.doc_count()
                for segment in index._segments():
                    ret['segments'].append(
                        {'id': segment.segid, 'entries': segment.doc_count()})
                for item in index.schema.items():
                    field_info = {
                        'name': item[0], 'type': item[1].__class__.__name__, 'range': [None, None]}
                    #values = list(searcher.lexicon(item[0]))
                    values = list(searcher.field_terms(item[0]))
                    #values_filtered = [v for v in values if repr(v) not in ['-2147483640L', '-2147483641L', '-2147483520L']]
                    values_filtered = values
                    if field_info['type'] == 'NUMERIC' and 'date' in field_info['name']:
                        values_filtered = [
                            v for v in values if v < 5000 and v > -5000]
                    if not values_filtered:
                        values_filtered = [0]
                    field_info['unique_values'] = len(list(values))
                    field_info['range'] = [repr(v)[0:12] for v in [
                        min(values_filtered), max(values_filtered)]]
                    ret['fields'].append(field_info)

                    if field_info['name'] == afield:
                        ret['values'] = sorted(list(set(values)))

                if query:
                    info = {}
                    ret['results'] = self.whoosh_search(
                        query, searcher, index, info)

        return ret

    def whoosh_search(self, query, searcher, index, info):
        ret = ''
        # run a whoosh search and display the hits
        # query applies to all fields in the schema
        # special query: ALL, ANY
        #
        limit = int(self.options['limit'] or '1000000')
        if query in ['ALL', 'ANY']:
            from whoosh.query.qcore import Every
            q = Every()
        else:
            from whoosh.qparser import MultifieldParser, GtLtPlugin

            # TODO: only active columns
            term_fields = [item[0] for item in index.schema.items()]
            parser = MultifieldParser(term_fields, index.schema)
            parser.add_plugin(GtLtPlugin)

            q = parser.parse(u'%s' % query)

        if query in ['ANY']:
            limit = 1

        afield = self.options['field']
        res = searcher.search(q, limit=limit)
        vs = {}
        for hit in res:
            if afield:
                # display only the unique value in the requested field
                vs[hit[afield]] = vs.get(hit[afield], 0) + 1
            else:
                # display all field, value in this record
                for k, v in hit.iteritems():
                    ret += '\t%-20s %s\n' % (k, repr(v)[0:30])
                ret += '\t' + ('-' * 20) + '\n'

        if vs:
            for v, c in vs.iteritems():
                ret += '\t%6s x %s\n' % (c, repr(v))

        info['results'] = ret
        info['result_size'] = len(res)

        ret += '\n\n%s documents found' % len(res)

        return ret

    def test(self, options):
        print 'test'
        from whoosh.index import open_dir
        index = open_dir(os.path.join(settings.SEARCH_INDEX_PATH, 'unified'))
        with index.searcher() as searcher:
            from whoosh.qparser import MultifieldParser

            #field_names = [field['whoosh']['name'] for field in self.get_fields_info().values()]
            field_names = ['description', 'repository', 'place']

            parser = MultifieldParser(field_names, index.schema)
            print index.schema.stored_names()
            query = parser.parse('vaticana')
            results = searcher.search(query, limit=None)
            print len(results)
            print results
            print results[0]
            # print results[0].highlights('recid')
            # print results[1].results
            #resultids = [result['recid'] for result in results]

    def index_all(self, options):
        for name in self.get_requested_index_names():
            self.index(name)

    def get_requested_index_names(self):
        #ret = ['unified', 'autocomplete']
        ret = ['unified']
        index_filter = self.options['index_filter']
        if index_filter:
            if index_filter not in ret:
                print 'ERROR: index not found (%s)' % index_filter
                exit()
            else:
                ret = [index_filter]

        return ret

    def get_requested_content_types(self):
        ''' Returns a list of content type classes.
            By default returns all the available classes.
            Unless the --ctf= is used to filter that list.
        '''
        from digipal.views.content_type.search_hands import SearchHands
        from digipal.views.content_type.search_manuscripts import SearchManuscripts
        from digipal.views.content_type.search_scribes import SearchScribes

        options = self.options

        content_type_filter = options['content_type_filter']
        if content_type_filter:
            types = []
            ctf = content_type_filter.title()
            for cl_name in [ctf, u'Search%s' % ctf, u'Search%ss' % ctf]:
                cl = locals().get(cl_name, None)
                if cl:
                    types.append(cl())
        else:
            types = [SearchHands(), SearchManuscripts(), SearchScribes()]

        if not types:
            print 'ERROR: Content Type not found (%s)' % content_type_filter
            exit()

        return types

    def search(self):
        from digipal.views.faceted_search import faceted_search
        cts = faceted_search.get_types(None)

        class Req(object):

            def __init__(self):
                self.META = {}
                self.GET = {}
                self.REQUEST = self.GET
                self.user = None

            def set_user(self, name):
                from django.contrib.auth.models import User
                self.user = User.objects.filter(username=name).first() or None

            def set_query_string(self, query_string):
                self.META['QUERY_STRING'] = query_string
                if query_string:
                    for pair in query_string.split('&'):
                        parts = pair.split('=')
                        if len(parts) == 2:
                            self.GET[parts[0]] = parts[1]

        request = Req()
        request.set_user(self.options['user'])
        request.set_query_string(self.options['qs'])

        for ct in faceted_search.get_types(None):
            if ct.get_key() == self.options['index_filter']:
                records = ct.get_requested_records(request)

                print '%s records found' % len(records)
                for record in records:
                    print record.id, repr(record)

    def index_facets(self, options):
        indexer = SearchIndexer()
        indexer.build_indexes(self.get_filtered_indexes())

    def index(self, index_name='unified'):
        types = self.get_requested_content_types()

        from whoosh.fields import TEXT, ID, NGRAM, NUMERIC
        from whoosh.analysis import StemmingAnalyzer, SimpleAnalyzer, IDAnalyzer
        from whoosh.analysis.filters import LowercaseFilter
        simp_ana = SimpleAnalyzer()
        print 'Building %s index...' % index_name

        # build a single schema from the fields exposed by the different search
        # types
        print '\tSchema:'
        fields = {}
        for type in types:
            for info in type.get_fields_info().values():
                if info['whoosh']['name'] not in fields and not info['whoosh'].get('ignore', False):
                    print '\t\t%s' % info
                    field_type = info['whoosh']['type']

                    if index_name == 'autocomplete':
                        # break the long text fields into terms, leave the
                        # others as single expression
                        if not (field_type.__class__ == NUMERIC):
                            if info.get('long_text', False):
                                field_type = TEXT(analyzer=simp_ana)
                            else:
                                field_type = ID(
                                    stored=True, analyzer=IDAnalyzer() | LowercaseFilter())
                    print '\t\t%s' % field_type
                    fields[info['whoosh']['name']] = field_type

                    # JIRA 508 - Add an ID counterpart to allow exact phrase search
#                     if info.get('long_text', False):
#                         fields[info['whoosh']['name']+'_iexact'] = ID(analyzer=IDAnalyzer(lowercase=True))

        from whoosh.fields import Schema
        schema = Schema(**fields)

        # Create the index schema
        index = self.recreate_index(index_name, schema)

        # Add documents to the index
        print '\tWrite indexes:'
        writer = index.writer()
        aci = {}
        for type in types:
            count = type.write_index(writer, self.is_verbose(), aci)
            print '\t\t%s %s records indexed' % (count, type.get_model().__name__)

        # autocomplete
        if index_name == 'unified':
            f = open(types[0].get_autocomplete_path(True), 'w')
            f.write((ur'|'.join(aci.keys())).encode('utf8'))
            f.close()

        writer.commit()

    def index_graph_description(self, index_name='graphs'):
        from whoosh.fields import TEXT, ID, NGRAM, NUMERIC, KEYWORD
        from whoosh.analysis import StemmingAnalyzer, SimpleAnalyzer, IDAnalyzer
        from whoosh.analysis.filters import LowercaseFilter
        print 'Building %s index...' % index_name

        # build a single schema from the fields exposed by the different search
        # types
        print '\tSchema:'
        fields = {'gid': ID(stored=True), 'description': KEYWORD(
            lowercase=True, scorable=True)}
        #fields = {'gid': ID(stored=True), 'description': TEXT(analyzer=SimpleAnalyzer(ur'[.\s]', True))}

        from whoosh.fields import Schema
        schema = Schema(**fields)

        # Create the index schema
        index = self.recreate_index(index_name, schema)

        # Add documents to the index
        print '\tWrite indexes:'
        writer = index.writer()
        c = 0
        from digipal.models import Graph
        for graph in Graph.objects.filter(graph_components__isnull=False).prefetch_related('graph_components', 'graph_components__component', 'graph_components__features').distinct():
            c += 1
            doc = {'gid': unicode(
                graph.id), 'description': graph.get_serialised_description()}
            writer.add_document(**doc)

        print '\t\tIndex %d graphs' % c

        writer.commit()

    def recreate_index(self, index_name, schema):
        ret = SearchIndexer.recreate_whoosh_index(
            settings.SEARCH_INDEX_PATH, index_name, schema)
        return ret

    def is_dry_run(self):
        return self.options.get('dry-run', False)

    def is_verbose(self):
        return int(self.options.get('verbosity', 1)) > 1

    def log(self, *args, **kwargs):
        self.logger.log(*args, **kwargs)
