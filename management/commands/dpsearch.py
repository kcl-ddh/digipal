from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import shlex
import subprocess
import re
from optparse import make_option
import utils
from utils import Logger  
from django.utils.datastructures import SortedDict
  

class Command(BaseCommand):
    help = """
Digipal search tool.
    
Commands:
    
  index
                        Re-Index all the content 

  info
                        Show general info and whoosh schemas
                        
  dump
                        Dump indices
                        
Options:
  
  --if=INDEX_NAME
                        Work only with index INDEX_NAME 

  --ctf=CONTENT_TYPE_NAME
                        Work only with content type CONTENT_TYPE_NAME
                        e.g. hand

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
            raise CommandError('Please provide a command. Try "python manage.py help dpsearch" for help.')
        command = args[0]
        
        known_command = False

        if command == 'index':
            known_command = True
            self.index_all(options)

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
            self.log('Nothing actually written (remove --dry-run option for permanent changes).', 1)
        
        if not known_command:
            print Command.help

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

    def info(self, options):
        from datetime import datetime
        
        print 'Indices:'
        for name in self.get_requested_index_names():
            print '\t%s' % name

        print 'Content Types:'
        for name in self.get_requested_content_types():
            print '\t%s' % name.__class__.__name__
        
        for dir in os.listdir(settings.SEARCH_INDEX_PATH):
            print 'Schemas - %s' % dir
            dir_abs = os.path.join(settings.SEARCH_INDEX_PATH, dir)

            print '\t%s' % dir_abs
            
            if os.path.isdir(dir_abs):
                # calculate the index size
                size = 0.0
                most_recent = 0
                for file in os.listdir(dir_abs):
                    try:
                        file_abs = os.path.join(dir_abs, file)
                        size += os.path.getsize(file_abs)
                        most_recent = max(most_recent, os.path.getmtime(file_abs))
                    except os.error:
                        pass
                size /= (1024.0 * 1024.0)
                print '\t%.2f MB %s' % (size, datetime.fromtimestamp(most_recent))
            
                # print the schema
                print
                from whoosh.index import open_dir
                index = open_dir(dir_abs)
                for item in index.schema.items():
                    print '\t%s' % repr(item)
            
            print
            

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
            #print results[0].highlights('recid')
            #print results[1].results
            #resultids = [result['recid'] for result in results]

    def index_all(self, options):
        for name in self.get_requested_index_names():
            self.index(name)
            
    def get_requested_index_names(self):
        ret = ['unified', 'autocomplete']
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
        
    def index(self, index_name='unified'):
        types = self.get_requested_content_types()
        
        from whoosh.fields import TEXT, ID, NGRAM, NUMERIC
        from whoosh.analysis import StemmingAnalyzer, SimpleAnalyzer, IDAnalyzer
        from whoosh.analysis.filters import LowercaseFilter
        simp_ana = SimpleAnalyzer()
        print 'Building %s index...' % index_name
        
        # build a single schema from the fields exposed by the different search types
        print '\tSchema:' 
        fields = {}
        for type in types:
            for info in type.get_fields_info().values():
                if info['whoosh']['name'] not in fields and not info['whoosh'].get('ignore', False):
                    print '\t\t%s' % info
                    field_type = info['whoosh']['type']
                    
                    if index_name == 'autocomplete':
                        # break the long text fields into terms, leave the others as single expression
                        if not (field_type.__class__ == NUMERIC):
                            if info.get('long_text', False):
                                field_type = TEXT(analyzer=simp_ana)
                            else:
                                field_type = ID(stored=True, analyzer=IDAnalyzer() | LowercaseFilter())
                    print '\t\t%s' % field_type          
                    fields[info['whoosh']['name']] = field_type
        
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
            
        f = open('ica.idx', 'w')
        f.write((ur'|'.join(aci.keys())).encode('utf8'))
        f.close()
        
        writer.commit()

    def index_graph_description(self, index_name='graphs'):
        from whoosh.fields import TEXT, ID, NGRAM, NUMERIC, KEYWORD
        from whoosh.analysis import StemmingAnalyzer, SimpleAnalyzer, IDAnalyzer
        from whoosh.analysis.filters import LowercaseFilter
        print 'Building %s index...' % index_name
        
        # build a single schema from the fields exposed by the different search types
        print '\tSchema:'
        fields = {'gid': ID(stored=True), 'description': KEYWORD(lowercase=True, scorable=True)}
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
            doc = {'gid': unicode(graph.id), 'description': graph.get_serialised_description()}
            writer.add_document(**doc)
        
        print '\t\tIndex %d graphs' % c
        
        writer.commit()

    def recreate_index(self, index_name, schema):
        import os.path
        from whoosh.index import create_in
        path = settings.SEARCH_INDEX_PATH
        if not os.path.exists(path):
            os.mkdir(path)
        path = os.path.join(path, index_name)
        if os.path.exists(path):
            import shutil
            shutil.rmtree(path)
        os.mkdir(path)
        print '\tCreated index under "%s"' % path
        # TODO: check if this REcreate the existing index
        index = create_in(path, schema)
        
        return index
        
    def is_dry_run(self):
        return self.options.get('dry-run', False)

    def is_verbose(self):
        return int(self.options.get('verbosity', 1)) > 1

    def log(self, *args, **kwargs):
        self.logger.log(*args, **kwargs)
