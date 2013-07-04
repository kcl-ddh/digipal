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

"""
    
    args = 'index'
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
            action='store_true',
            dest='dry-run',
            default=False,
            help='Dry run, don\'t change any data.'),
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
            self.index(options)

        if command == 'test':
            known_command = True
            self.test(options)

        if self.is_dry_run():
            self.log('Nothing actually written (remove --dry-run option for permanent changes).', 1)

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

    def index(self, options):
        from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS
        print 'Indexing...'
        
        from digipal.views.content_type.search_hands import SearchHands
        from digipal.views.content_type.search_manuscripts import SearchManuscripts
        from digipal.views.content_type.search_scribes import SearchScribes
        #types = [SearchHands(), SearchManuscripts(), SearchScribes()]
        types = [SearchHands()]
        
        # build a single schema from the fields exposed by the different search types
        print 'Schema:' 
        fields = {}
        for type in types:
            for info in type.get_fields_info().values():
                print '\t%s' % info
                fields[info['whoosh']['name']] = info['whoosh']['type']
        
        from whoosh.fields import Schema
        schema = Schema(**fields)
        
        # create the index
        import os.path
        from whoosh.index import create_in
        path = settings.SEARCH_INDEX_PATH
        if not os.path.exists(path):
            os.mkdir(path)
        path = os.path.join(path, 'unified')
        if os.path.exists(path):
            import shutil
            shutil.rmtree(path)
        os.mkdir(path)
        print 'Created index under "%s"' % path
        # TODO: check if this REcreate the existing index
        index = create_in(path, schema)
        
        # Write the index
        print 'Write indexes:'
        writer = index.writer()
        for type in types:
            count = type.write_index(writer)
            print '\t%s %s records indexed' % (count, type.get_model())
        
        writer.commit()

    def is_dry_run(self):
        return self.options.get('dry-run', False)
    
    def log(self, *args, **kwargs):
        self.logger.log(*args, **kwargs)
