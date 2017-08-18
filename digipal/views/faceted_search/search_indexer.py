from digipal import utils as dputils
from digipal.templatetags.hand_filters import chrono
from digipal.models import KeyVal
from digipal.views.faceted_search import faceted_search
from datetime import datetime
import os

'''
    SearchIndexer
    
    Used to rebuild the indexes used by the faceted search
    
    Usage:
    
        si = SearchIndexer()
        si.build_indexes(['images', 'manuscripts'])
'''


class SearchIndexer(object):

    date_format = '%d-%m-%Y %H:%M:%S'

    def build_indexes(self, index_filter=[]):
        ''' Rebuild indexes based on the keys in index_filter. All if index_filter is empty'''
        self.indexable_types = []
        for ct in faceted_search.get_types(True):
            if not index_filter or ct.key in index_filter:
                self.indexable_types.append(ct)

        self.write_state_initial()
        for ct in self.indexable_types:
            self.write_state_update(ct, 0.001)

            self.create_index_schema(ct)
            self.populate_index(ct)
            self.optimize_index(ct)

            self.write_state_update(ct, 1.0)

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
        from mezzanine.conf import settings
        ret = self.recreate_whoosh_index(os.path.join(
            settings.SEARCH_INDEX_PATH, 'faceted'), ct.key, Schema(**fields))
        return ret

    def populate_index(self, ct, index=None):
        chrono('POPULATE_INDEX:')

        # Add documents to the index
        print '\tgenerate sort rankings'

        chrono('RANK_VALUES:')
        ct.prepare_value_rankings(callback=lambda progress: self.write_state_update(
            ct, max(0.001, 1.0 / 3.0 * progress)))
        chrono(':RANK_VALUES')

        chrono('INDEXING QUERY:')
        print '\tretrieve all records'
        dputils.gc_collect()

        from whoosh.writing import BufferedWriter
        rcs = ct.get_all_records(True)
        record_count = rcs.count()

        writer = None

        chrono(':INDEXING QUERY')

        print '\tadd records to index'

        i = 0
        commit_size = 500
        progress_size = 200

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
            pbar.update(i + 1)

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

            if (i % progress_size) == 0:
                self.write_state_update(
                    ct, (1 + 1.0 * i / record_count) * 1.0 / 3)

        if writer:
            writer.commit(merge=False)
        #rcs = None
        # ct.clear_value_rankings()

        pbar.complete()
        chrono(':INDEXING')

        print '\n'

        chrono(':POPULATE_INDEX')

        print '\tdone (%s records)' % record_count

    def optimize_index(self, ct):
        self.write_state_update(ct, 1.0 / 3 * 2)
        dputils.gc_collect()
        index = ct.get_whoosh_index()
        print '\toptimize index'
        writer = index.writer()
        writer.commit(optimize=True)

    @classmethod
    def recreate_whoosh_index(cls, path, index_name, schema):
        from whoosh.index import create_in
        if not os.path.exists(path):
            os.makedirs(path)
        path = os.path.join(path, index_name)
        if os.path.exists(path):
            import shutil
            shutil.rmtree(path)
        os.makedirs(path)
        print '\tCreated index under "%s"' % path
        # TODO: check if this REcreate the existing index
        index = create_in(path, schema)

        return index

    @classmethod
    def get_whoosh_field_types(cls, field):
        ret = {}

        whoosh_sortable_field = faceted_search.FacetedModel._get_sortable_whoosh_field(
            field)
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
            # | is NECESSARY for multivalued fields
            ret = TEXT(analyzer=SimpleAnalyzer(
                ur'[/.\s()\u2013\u2014|-]', True), stored=True, sortable=sortable)
        elif field_type == 'title':
            # A title (e.g. British Library)
            # Accepts variants and partial search (e.g. 'libraries')
            ret = TEXT(analyzer=StemmingAnalyzer(minsize=1, stoplist=None) | CharsetFilter(
                accent_map), stored=True, sortable=sortable)
        elif field_type == 'short_text':
            # A few words.
            ret = TEXT(analyzer=StemmingAnalyzer(minsize=2) | CharsetFilter(
                accent_map), stored=True, sortable=sortable)
        elif field_type == 'xml':
            # plain text derived from XML document
            ret = TEXT(analyzer=StemmingAnalyzer(minsize=2) | CharsetFilter(
                accent_map), stored=True, sortable=sortable)
        elif field_type == 'boolean':
            # 0|1
            ret = NUMERIC(stored=True, sortable=sortable)
        else:
            ret = TEXT(analyzer=StemmingAnalyzer(minsize=2) | CharsetFilter(
                accent_map), stored=True, sortable=sortable)

        return ret

    #-----------------------
    # STATE
    #-----------------------

    if 0:
        state = {
            'pid': 0,
            'state': 'queued|indexing|indexed',
            'progress': 0.9,
            'started': '',
            'updated': '',
            'indexes': {
                'INDEXKEY': {
                    'state': 'queued|indexing|indexed',
                    'progress': 0.9,
                    'started': ''
                },
                # ...
            }
        }

    def write_state_initial(self):
        state = self.get_state_initial([ct.key for ct in self.indexable_types])

        self.write_state(state)
        self.state = state

    def get_state_initial(self, index_keys):
        state = {
            'pid': os.getpid(),
            'state': 'queued',
            'progress': 0.0,
            'started': datetime.now(),
            'indexes': {
            }
        }
        for index_key in index_keys:
            state['indexes'][index_key] = {
                'state': 'queued',
                'progress': 0.0,
                'started': None,
            }

        return state

    def write_state_update(self, ct, progress):
        self.state['indexes'][ct.key]['progress'] = progress
        self.write_state(self.state)

    def clear_state(self):
        KeyVal.setjs('indexer', {})

    def read_state(self):
        ret = KeyVal.getjs('indexer')
        self.convert_state_dates_to_objects(ret)
        return ret

    def write_state(self, state):
        state['updated'] = datetime.now()
        state['progress'] = 1.0 * sum([idx['progress']
                                       for idx in state['indexes'].values()]) / len(state['indexes'].keys())
        state['state'] = None
        for idx in state['indexes'].values():
            if idx['progress'] == 0.0:
                idx['state'] = 'queued'
            if idx['progress'] > 0.0:
                idx['state'] = 'indexing'
            if idx['progress'] == 1.0:
                idx['state'] = 'indexed'
            if state['state'] not in [None, idx['state']]:
                state['state'] = 'indexing'
            else:
                state['state'] = idx['state']

        # json conversion doesn't understand python dates
        self.convert_state_dates_to_strings(state)
        # print '-' * 20
        # print state
        KeyVal.setjs('indexer', state)
        self.convert_state_dates_to_objects(state)

    def convert_state_dates_to_strings(self, state):
        if not state:
            return

        def get_str_from_date(adate):
            ret = None
            if adate:
                ret = adate.strftime(self.date_format)
            return ret

        state['started'] = get_str_from_date(state['started'])
        state['updated'] = get_str_from_date(state['updated'])
        for idx in state['indexes'].values():
            idx['started'] = get_str_from_date(idx['started'])

    def convert_state_dates_to_objects(self, state):
        if not state:
            return

        def get_date_from_str(adate):
            ret = None
            if adate:
                ret = datetime.strptime(adate, self.date_format)
            return ret
        state['started'] = get_date_from_str(state['started'])
        state['updated'] = get_date_from_str(state['updated'])
        for idx in state['indexes'].values():
            idx['started'] = get_date_from_str(idx['started'])
