from digipal import utils as dputils
from digipal.templatetags.hand_filters import chrono
from digipal.models import KeyVal
from digipal.views.faceted_search import faceted_search
import os

'''
    SearchIndexer
    
    Used to rebuild the indexes used by the faceted search
    
    Usage:
    
        si = SearchIndexer()
        si.build_indexes(['images', 'manuscripts'])
'''
class SearchIndexer(object):
    # TODO: move the above indexing functions to this class

    if 0:
        state = {
            'pid': 0,
            'state': 'queued|indexing|indexed',
            'progress': 0.9,
            'indexes': {
                'INDEXKEY': {
                    'state': 'queued|indexing|indexed',
                    'progress': 0.9,
                },
                # ...
            }
        }
    
    def get_state(self):
        ret = KeyVal.get('indexer') 
        return ret

    def set_state(self, state):
        KeyVal.set('indexer', state)
        
    def build_indexes(self, index_filter=[]):
        ''' Rebuild the indexes which key is in index_filter. All if index_filter is empty'''
        for ct in faceted_search.get_types(True):
            if not index_filter or ct.key in index_filter:
                #index = create_index_schema(ct)
                self.create_index_schema(ct)
    #             if index:
                if 1:
                    #populate_index(ct, index)
                    self.populate_index(ct)
                    #index = None
                    self.optimize_index(ct)
    
    def create_index_schema(self, ct):
        print '%s' % ct.key
    
        print '\tcreate schema'
    
        # create schema
        from whoosh.fields import TEXT, ID, NGRAM, NUMERIC, KEYWORD
        fields = {'id': ID(stored=True)}
        for field in ct.fields:
            if ct.is_field_indexable(field):
                for suffix, whoosh_type in self.get_whoosh_field_types(field).iteritems():
                    fields[field['key'] + suffix] = whoosh_type
    
        print '\t' + ', '.join(key for key in fields.keys())
    
        print '\trecreate empty index'
    
        # recreate an empty index
        from whoosh.fields import Schema
        from django.conf import settings
        ret = self.recreate_whoosh_index(os.path.join(settings.SEARCH_INDEX_PATH, 'faceted'), ct.key, Schema(**fields))
        return ret
    
    def populate_index(self, ct, index=None):
        chrono('POPULATE_INDEX:')
    
        # Add documents to the index
        print '\tgenerate sort rankings'
    
        chrono('RANK_VALUES:')
        ct.prepare_value_rankings()
        chrono(':RANK_VALUES')
    
        chrono('INDEXING QUERY:')
        print '\tretrieve all records'
        dputils.gc_collect()
    
        from whoosh.writing import BufferedWriter
        # writer = BufferedWriter(index, period=None, limit=20)
        rcs = ct.get_all_records(True)
        record_count = rcs.count()
    
        #writer = index.writer()
        writer = None
    
        chrono(':INDEXING QUERY')
    
        print '\tadd records to index'
    
        i = 0
        #commit_size = 1000000
        commit_size = 500
    
        # settings.DEV_SERVER = True
        chrono('INDEXING:')
        chrono('First record:')
    
        record_condition = ct.get_option('condition', None)
    
        pbar = dputils.ProgressBar(record_count)
    
        # Indexing can use n x 100 MB
        # Which can be excessive for small VMs
        # One technique is to create small, independent index segments
        # Then optimise them outside this fct on a separate index
        for record in rcs.iterator():
            if i == 0:
                chrono(':First record')
            pbar.update(i+1)
    
            if (i % commit_size) == 0:
                # we have to commit every x document otherwise the memory saturates on the VM
                # BufferedWriter is buggy and will crash after a few 100x docs
                if writer:
                    writer.commit(merge=False)
    
                # we have to recreate after commit because commit unlock index
                writer = None
                index = None
                dputils.gc_collect()
    
                index = ct.get_whoosh_index()
                writer = index.writer()
    
            i += 1
    
            if record_condition and not record_condition(record):
                continue
    
            writer.add_document(**ct.get_document_from_record(record))
    
        if writer:
            writer.commit(merge=False)
        #rcs = None
        #ct.clear_value_rankings()
    
        pbar.complete()
        chrono(':INDEXING')
    
        print '\n'
    
        chrono(':POPULATE_INDEX')
    
        print '\tdone (%s records)' % record_count

    def optimize_index(self, ct):
        dputils.gc_collect()
        index = ct.get_whoosh_index()
        print '\toptimize index'
        writer = index.writer()
        writer.commit(optimize=True)

    @classmethod
    def recreate_whoosh_index(cls, path, index_name, schema):
        from whoosh.index import create_in
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

    @classmethod
    def get_whoosh_field_types(cls, field):
        ret = {}
    
        whoosh_sortable_field =  faceted_search.FacetedModel._get_sortable_whoosh_field(field)
        sortable = (whoosh_sortable_field == field['key'])
    
        if field['type'] == 'date':
            ret[''] = cls.get_whoosh_field_type({'type': 'code'})
            ret['_min'] = cls.get_whoosh_field_type({'type': 'int'}, True)
            ret['_max'] = cls.get_whoosh_field_type({'type': 'int'}, True)
            ret['_diff'] = cls.get_whoosh_field_type({'type': 'int'}, True)
        else:
            ret[''] = cls.get_whoosh_field_type(field)
    
        if whoosh_sortable_field and not sortable:
            ret['_sortable'] = cls.get_whoosh_field_type({'type': 'int'}, True)
    
        return ret
    
    @classmethod
    def get_whoosh_field_type(cls, field, sortable=False):
        '''
        Defines Whoosh field types used to define the schemas.
        See get_field_infos().
        '''
    
        # see http://pythonhosted.org/Whoosh/api/analysis.html#analyzers
        # see JIRA 165
    
        from whoosh.fields import TEXT, ID, NUMERIC, BOOLEAN
        # TODO: shall we use stop words? e.g. 'A and B' won't work?
        from whoosh.analysis import SimpleAnalyzer, StandardAnalyzer, StemmingAnalyzer, CharsetFilter, RegexTokenizer
        from whoosh.support.charset import accent_map
        # ID: as is; SimpleAnalyzer: break into lowercase terms, ignores punctuations; StandardAnalyzer: + stop words + minsize=2; StemmingAnalyzer: + stemming
        # minsize=1 because we want to search for 'Scribe 2'
    
        # A paragraph or more.
        field_type = field['type']
        if field_type == 'id':
            # An ID (e.g. 708-AB)
            # EXACT search only
            analyzer = None
            if field.get('multivalued', False):
                analyzer = RegexTokenizer(ur'\|', gaps=True)
            ret = ID(stored=True, sortable=sortable, analyzer=analyzer)
        elif field_type in ['int']:
            ret = NUMERIC(sortable=sortable)
        elif field_type in ['code']:
            # A code (e.g. K. 402, Royal 7.C.xii)
            # Accepts partial but exact search (e.g. royal)
            # See JIRA 358
            ret = TEXT(analyzer=SimpleAnalyzer(ur'[/.\s()\u2013\u2014-]', True), stored=True, sortable=sortable)
        elif field_type == 'title':
            # A title (e.g. British Library)
            # Accepts variants and partial search (e.g. 'libraries')
            ret = TEXT(analyzer=StemmingAnalyzer(minsize=1, stoplist=None) | CharsetFilter(accent_map), stored=True, sortable=sortable)
        elif field_type == 'short_text':
            # A few words.
            ret = TEXT(analyzer=StemmingAnalyzer(minsize=2) | CharsetFilter(accent_map), stored=True, sortable=sortable)
        elif field_type == 'xml':
            # xml document.
            ret = TEXT(analyzer=StemmingAnalyzer(minsize=2) | CharsetFilter(accent_map), stored=True, sortable=sortable)
        elif field_type == 'boolean':
            # 0|1
            ret = NUMERIC(stored=True, sortable=sortable)
        else:
            ret = TEXT(analyzer=StemmingAnalyzer(minsize=2) | CharsetFilter(accent_map), stored=True, sortable=sortable)
    
        return ret
