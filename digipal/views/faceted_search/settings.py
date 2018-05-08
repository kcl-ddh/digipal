import re
from copy import deepcopy

FACETED_SEARCH = {
    'fragments': {
        'overview': {'icon': 'stats', 'label': 'Overview', 'key': 'overview', 'page_sizes': [-1]},
        'view_default': {'icon': 'list', 'label': 'List View', 'key': 'list'},

        'field_mapping_empty': {None: 'unspecified', '': 'unspecified'},
    },
}


def get_fragment(key, default=None, original=False):
    ret = FACETED_SEARCH['fragments'].get(key, default)
    if not original:
        ret = deepcopy(ret)
    return ret


FACETED_SEARCH.update({
    'visualisation': {
        # VISUALISATION SETTINGS
        'field_x': 'hi_date',
        'field_conflate': 'item_part',
        # a list of facet keys that can be used to categorise the visualisation
        # e.g. ['hi_type', 'clause_type', 'medieval_archive', 'issuer', 'issuer_type'],
        # if empty, all possible facets are available
        'categories': [],
    },
    'types': [
        # label = the label displayed on the screen
        # label_col = the label in the column in the result table
        # type = the type of the field

        # path = a field name (can go through a related object or call
        # a function)

        # filter = True to show a facet widget that lets the user filter by this field (e.g. facets with options or range)
        # hide_options = True we don't show the options in the facet widget (e.g. a slider / text box)
        #    see areFieldOptionsShown()
        # count = True to show the number of hits for each option => implies filter = True
        # search = True if the field can be searched on (phrase query)
        # viewable = True if the field can be displayed in the result set
        # request = True if the path ends with a method that takes the
        # request as an argument

        # index = True iff (search or filter or count)

        # link_to_record = if True, thumb links to record instead of image page
        #  (only for field.type=image)

        # expanded = 1 to show all option in the facet by default,
        #    0 to show first 5, -1 to collapse the facet
        #    2 always expanded

        # e.g. ann: viewable, full_size: count, repo_city: viewable+count+search
        # id: special
        # Most of the times viewable => searchable but not always (e.g.
        # ann.)

        {
            #'disabled': True,
            # if private is True, the type is visible to editors only
            #'private': False,
            'key': 'manuscripts',
            'label': 'Manuscript',
            'model': 'digipal.models.ItemPart',
            'fields': [
                {'key': 'url', 'label': 'Address', 'label_col': ' ',
                 'path': 'get_absolute_url', 'type': 'url', 'viewable': True},

                {'key': 'hi_has_images', 'label': 'Image Availablity',
                 'path': 'get_has_public_image_label', 'type': 'code', 'count': True},

                {'key': 'hi_date', 'label': 'MS Date', 'path': 'historical_item.get_date_sort', 'type': 'date', 'filter': True,
                 'hide_options': True, 'viewable': True, 'search': True, 'id': 'hi_date', 'min': 500, 'max': 1300},
                {'key': 'hi_index', 'label': 'Cat. Num.', 'path': 'historical_item.catalogue_number',
                 'type': 'code', 'viewable': True, 'search': True},
                # id to avoid clashes on partials (e.g. brieve/charter
                # vs brieve-charter)
                {'key': 'hi_type', 'label': 'Document Type', 'path': 'historical_item.historical_item_type.name',
                 'type': 'id', 'viewable': True, 'count': True},
                {'key': 'hi_format', 'label': 'Format', 'path': 'historical_item.historical_item_format.name',
                 'type': 'code', 'viewable': True, 'count': True},
                {'key': 'repo_city', 'label': 'Repository City', 'path': 'current_item.repository.place.name',
                 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                {'key': 'repo_place', 'label': 'Repository', 'path': 'current_item.repository.human_readable',
                 'path_result': 'current_item.repository.name', 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                {'key': 'shelfmark', 'label': 'Shelfmark', 'path': 'current_item.shelfmark',
                 'search': True, 'viewable': True, 'type': 'code'},
                {'key': 'locus', 'label': 'Locus', 'path': 'locus',
                 'search': True, 'viewable': True, 'type': 'code'},
                {'key': 'hi_image_count', 'label_col': 'Public Images', 'label': 'Public Images',
                 'path': 'get_non_private_image_count', 'type': 'int', 'viewable': True},
                #{'key': 'annotations', 'label_col': 'Ann.', 'label': 'Annotations', 'path': 'hands_set.all.count', 'type': 'int', 'viewable': True},
                #{'key': 'thumbnail', 'label_col': 'Thumb.', 'label': 'Thumbnail', 'path': '', 'type': 'image', 'viewable': True, 'max_size': 70},

                # experiment for SJB - 12/2/16
                #{'key': 'allograph', 'label': 'Allograph', 'path': 'hands.all.graphs.all.idiograph.allograph.human_readable', 'viewable': False, 'type': 'title', 'count': True, 'search': True, 'multivalued': True},
            ],
            'select_related': ['current_item__repository__place'],
            'prefetch_related': ['historical_items', 'historical_items__historical_item_format', 'historical_items__historical_item_type', 'images'],
            #'filter_order': ['hi_date', 'full_size', 'hi_type', 'hi_format', 'repo_city', 'repo_place'],
            #'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'locus', 'hi_date', 'annotations', 'hi_format', 'hi_type', 'thumbnail'],
            'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'locus', 'hi_index', 'hi_date', 'hi_format', 'hi_type', 'hi_image_count'],
            'sorted_fields': ['repo_city', 'repo_place', 'shelfmark', 'locus'],
        },

        {
            #'disabled': True,
            'key': 'images',
            'label': 'Image',
            'model': 'digipal.models.Image',
            'django_filter': {'item_part__isnull': False},
            'fields': [

                {'key': 'url', 'label': 'Address', 'label_col': ' ',
                 'path': 'get_absolute_url', 'type': 'url', 'viewable': True},
                #{'key': 'scribe', 'label': 'Scribe', 'path': 'hands__scribes__count', 'faceted': True, 'index': True},
                #{'key': 'annotation', 'label': 'Annotations', 'path': 'annotations__count01', 'faceted': True, 'index': True},
                #
                {'key': 'hi_date', 'label': 'MS Date', 'path': 'item_part.historical_item.get_date_sort', 'type': 'date',
                 'filter': True, 'viewable': True, 'search': True, 'id': 'hi_date', 'min': 500, 'max': 1300},
                #{'key': 'img_is_public', 'label': 'Full Image', 'path': 'is_media_public', 'type': 'boolean', 'count': True, 'search': True},
                {'key': 'mp_permission', 'label': 'Availability',
                 'path': 'get_media_permission.get_permission_label', 'type': 'code', 'count': True},
                {'key': 'hi_type', 'label': 'Document Type', 'path': 'item_part.historical_item.historical_item_type.name',
                 'type': 'id', 'viewable': True, 'count': True},
                {'key': 'hi_format', 'label': 'Format', 'path': 'item_part.historical_item.historical_item_format.name',
                 'type': 'code', 'viewable': True, 'count': True},
                {'key': 'repo_city', 'label': 'Repository City', 'path': 'item_part.current_item.repository.place.name',
                 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                {'key': 'repo_place', 'label': 'Repository', 'path': 'item_part.current_item.repository.human_readable',
                 'path_result': 'item_part.current_item.repository.name', 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                {'key': 'shelfmark', 'label': 'Shelfmark', 'path': 'item_part.current_item.shelfmark',
                 'search': True, 'viewable': True, 'type': 'code'},
                {'key': 'locus', 'label': 'Locus', 'path': 'locus',
                 'search': True, 'viewable': True, 'type': 'code',
                 'sort_fct': lambda r: u'%s %s %s' % (
                     r.folio_number or '', r.folio_side or '', r.locus or ''
                 ),
                 'mapping': get_fragment('field_mapping_empty')},
                {'key': 'annotations', 'label_col': 'Ann.', 'label': 'Annotations',
                 'path': 'annotation_set.all.count', 'type': 'int', 'viewable': True},
                {'key': 'thumbnail', 'label_col': 'Thumb.', 'label': 'Thumbnail',
                 'path': '', 'type': 'image', 'viewable': True, 'max_size': 70},

                {'key': 'PRIVATE', 'label': 'Private',
                 'path': 'is_media_private', 'type': 'boolean', 'search': True},

            ],
            'select_related': ['item_part__current_item__repository__place'],
            'prefetch_related': ['item_part__historical_items', 'item_part__historical_items__historical_item_format', 'item_part__historical_items__historical_item_type'],
            'filter_order': ['hi_date', 'mp_permission', 'hi_type', 'hi_format', 'repo_city', 'repo_place'],
            'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'locus', 'hi_date', 'annotations', 'hi_format', 'hi_type', 'thumbnail'],
            #'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'locus', 'hi_date'],
            'sorted_fields': ['repo_city', 'repo_place', 'shelfmark', 'locus'],
            'views': [
                get_fragment('view_default'),
                {'icon': 'th', 'label': 'Grid View',
                 'key': 'grid', 'type': 'grid'},
                {'icon': 'picture', 'label': 'Zoom View',
                 'key': 'zoom', 'type': 'zoom', 'page_sizes': [1]},
            ],
        },

        {
            #'disabled': True,
            'key': 'scribes',
            'label': 'Scribe',
            'model': 'digipal.models.Scribe',
            'fields': [

                {'key': 'url', 'label': 'Address', 'label_col': ' ',
                 'path': 'get_absolute_url', 'type': 'url', 'viewable': True},

                {'key': 'scribe', 'label': 'Scribe', 'path': 'name',
                 'type': 'title', 'viewable': True, 'search': True},

                {'key': 'scribe_date', 'label': 'Date assigned to Scribe', 'path': 'date', 'type': 'date',
                 'viewable': True, 'filter': True, 'min': 900, 'max': 1200, 'id': 'scribe_date'},

                {'key': 'scriptorium', 'label': 'Scriptorium', 'path': 'scriptorium.name',
                 'type': 'title', 'viewable': True, 'search': True, 'count': True},

            ],
            #'select_related': ['item_part__current_item__repository__place'],
            #'prefetch_related': ['item_part__historical_items', 'item_part__historical_items__historical_item_format', 'item_part__historical_items__historical_item_type'],
            #'filter_order': ['hi_date', 'full_size', 'hi_type', 'hi_format', 'repo_city', 'repo_place'],
            #'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'locus', 'hi_date', 'annotations', 'hi_format', 'hi_type', 'thumbnail'],
            #'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'locus', 'hi_date'],
            'sorted_fields': ['scribe'],
        },

        {
            #'disabled': True,
            'key': 'hands',
            'label': 'Hand',
            'model': 'digipal.models.Hand',
            #'condition': lambda r: max([len(d.description or '') for d in r.descriptions.all()] or [0]) > 2,
            'fields': [

                {'key': 'url', 'label': 'Address', 'label_col': ' ',
                 'path': 'get_absolute_url', 'type': 'url', 'viewable': True},

                {'key': 'hand', 'label': 'Hand', 'path': 'get_search_label',
                 'type': 'title', 'viewable': True, 'search': True},

                #{'key': 'full_size', 'label': 'Image', 'path': 'get_media_right_label', 'type': 'boolean', 'count': True, 'search': True},
                #{'key': 'hi_type', 'label': 'Document Type', 'path': 'item_part.historical_item.historical_item_type.name', 'type': 'code', 'viewable': True, 'count': True},
                #{'key': 'hi_format', 'label': 'Format', 'path': 'item_part.historical_item.historical_item_format.name', 'type': 'code', 'viewable': True, 'count': True},
                {'key': 'repo_city', 'label': 'Repository City', 'path': 'item_part.current_item.repository.place.name',
                 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                {'key': 'repo_place', 'label': 'Repository', 'path': 'item_part.current_item.repository.human_readable',
                 'path_result': 'item_part.current_item.repository.name', 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                {'key': 'shelfmark', 'label': 'Shelfmark', 'path': 'item_part.current_item.shelfmark',
                 'search': True, 'viewable': True, 'type': 'code'},
                {'key': 'hand_label', 'label': 'Description', 'path': 'label',
                 'search': True, 'viewable': True, 'type': 'code', 'count': False},
                {'key': 'hand_place', 'label': 'Medieval Place', 'path': 'assigned_place.name',
                 'search': True, 'viewable': True, 'type': 'code', 'count': True},

                {'key': 'hand_date', 'label': 'Date', 'path': 'assigned_date.date', 'type': 'date',
                 'filter': True, 'viewable': True, 'search': True, 'id': 'hi_date', 'min': 680, 'max': 1200},

                {'key': 'index', 'label': 'Cat. Num.', 'path': 'item_part.historical_item.catalogue_number',
                 'search': True, 'viewable': True, 'type': 'code'},

                #{'key': 'locus', 'label': 'Locus', 'path': 'locus', 'search': True, 'viewable': True, 'type': 'code'},
                #{'key': 'annotations', 'label_col': 'Ann.', 'label': 'Annotations', 'path': 'hands_set.all.count', 'type': 'int', 'viewable': True},
                #{'key': 'thumbnail', 'label_col': 'Thumb.', 'label': 'Thumbnail', 'path': '', 'type': 'image', 'viewable': True, 'max_size': 70},
            ],
            'select_related': ['item_part__current_item__repository__place', 'assigned_place', 'assigned_date'],
            'prefetch_related': ['item_part__historical_items'],
            'filter_order': ['hand_date', 'repo_city', 'repo_place', 'hand_place'],
            #'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'locus', 'hi_date', 'annotations', 'hi_format', 'hi_type', 'thumbnail'],
            #'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'locus', 'hi_date'],
            'sorted_fields': ['hand', 'repo_city', 'repo_place', 'shelfmark'],
        },

        {
            #'disabled': True,
            'key': 'texts',
            'label': 'Text',
            'model': 'digipal_text.models.TextContentXML',
            'condition': lambda r: r.content and re.search('[a-z]', r.content),
            # TODO: temporary!
            #'django_filter': {'text_content__type__slug': 'transcription'},
            'fields': [

                {'key': 'url', 'label': 'Address', 'label_col': ' ',
                 'path': 'text_content.get_absolute_url', 'type': 'url', 'viewable': True},

                {'key': 'hi_index', 'label': 'Cat. Num.', 'path': 'text_content.item_part.historical_item.catalogue_number',
                 'type': 'code', 'viewable': True, 'search': True},
                {'key': 'hi_type', 'label': 'Document Type', 'path': 'text_content.item_part.historical_item.historical_item_type.name',
                 'type': 'id', 'viewable': True, 'count': True},
                {'key': 'repo_city', 'label': 'Repository City', 'path': 'text_content.item_part.current_item.repository.place.name',
                 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                {'key': 'repo_place', 'label': 'Repository', 'path': 'text_content.item_part.current_item.repository.human_readable',
                 'path_result': 'text_content.item_part.current_item.repository.name', 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                {'key': 'shelfmark', 'label': 'Shelfmark', 'path': 'text_content.item_part.current_item.shelfmark',
                 'search': True, 'viewable': True, 'type': 'code'},
                {'key': 'text_type', 'label': 'Text Type', 'path': 'text_content.type.name',
                 'search': True, 'viewable': True, 'type': 'code', 'count': True},
                {'key': 'hi_date', 'label': 'MS Date', 'path': 'text_content.item_part.historical_item.get_date_sort',
                 'type': 'date', 'filter': True, 'viewable': True, 'search': True, 'id': 'hi_date', 'min': 500, 'max': 1300},

                {'key': 'content', 'label': 'Content', 'path': 'content',
                 'search': True, 'viewable': True, 'type': 'xml'},

                {'key': 'PRIVATE', 'label': 'Private',
                 'path': 'is_private', 'type': 'boolean', 'search': True},

                #{'key': 'text_title', 'label': 'Title', 'path': 'text_content.__unicode__', 'type': 'title', 'viewable': True, 'search': True},
                {'key': 'thumbnail', 'label_col': 'Thumb.', 'label': 'Thumbnail',
                 'path': 'text_content.item_part.get_first_image', 'type': 'image', 'viewable': True, 'max_size': 70},

            ],
            'select_related': ['text_content__item_part__current_item__repository__place', 'text_content__type'],
            #'prefetch_related': ['item_part__historical_items'],
            #                     'filter_order': ['hand_date', 'repo_city', 'repo_place', 'hand_place'],
            #                     #'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'locus', 'hi_date', 'annotations', 'hi_format', 'hi_type', 'thumbnail'],
            #                     #'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'locus', 'hi_date'],
            'sorted_fields': ['repo_city', 'repo_place', 'shelfmark', 'text_type'],
            'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'text_type', 'hi_date', 'thumbnail'],
            'views': [
                get_fragment('view_default'),
                {'icon': 'th-list', 'label': 'Snippet View', 'key': 'snippet',
                 'template': 'list', 'params': {'snippets': 1}, 'type': 'snippets'},
            ],
        },

        {
            # Disabled as this is an ABSTRACT type, only used to create
            # concrete derivatives, see TextUnit class for more info.
            'disabled': True,
            'key': 'textunits',
            'label': 'Text Unit',
            #'model': 'mofa.customisations.digipal_text.models.Clause',
            'model': 'digipal_text.models.TextUnit',
            'fields': [
                {'key': 'url', 'label': 'Address', 'label_col': ' ',
                 'path': 'get_absolute_url', 'type': 'url', 'viewable': True, 'rowspan': '3'},
                {'key': 'hi_index', 'label': 'Cat. Num.', 'path': 'content_xml.text_content.item_part.historical_item.catalogue_number',
                 'type': 'code', 'viewable': True, 'search': True},
                {'key': 'hi_type', 'label': 'Document Type', 'path': 'content_xml.text_content.item_part.historical_item.historical_item_type.name',
                 'type': 'id', 'viewable': True, 'count': True},
                {'key': 'repo_city', 'label': 'Repository City', 'path': 'content_xml.text_content.item_part.current_item.repository.place.name',
                 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                {'key': 'repo_place', 'label': 'Repository', 'path': 'content_xml.text_content.item_part.current_item.repository.human_readable',
                 'path_result': 'content_xml.text_content.item_part.current_item.repository.name', 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                {'key': 'shelfmark', 'label': 'Shelfmark', 'path': 'content_xml.text_content.item_part.current_item.shelfmark',
                 'search': True, 'viewable': True, 'type': 'code'},
                {'key': 'hi_date', 'label': 'MS Date', 'path': 'content_xml.text_content.item_part.historical_item.get_date_sort',
                 'type': 'date', 'filter': True, 'viewable': True, 'search': True, 'id': 'hi_date', 'min': 500, 'max': 1300},
                {'key': 'text_type', 'label': 'Text Type', 'path': 'content_xml.text_content.type.name',
                 'search': True, 'viewable': True, 'type': 'code', 'count': True},
                #{'key': 'unitid', 'label': 'Ref', 'path': 'unitid', 'search': True, 'viewable': True, 'type': 'code'},
                {'key': 'content', 'label': 'Content', 'path': 'content', 'search': True,
                 'viewable': True, 'type': 'xml', 'line': 2, 'classes': 'mce-content-body preview'},
                #{'key': 'content', 'label': 'Content', 'path': 'content', 'search': True, 'viewable': True, 'type': 'text', 'line': 2},
                {'key': 'thumbnail', 'label': 'thumbnail', 'path': 'get_thumb', 'search': False,
                 'viewable': True, 'type': 'image', 'line': 1, 'link': True, 'request': True},
                {'key': 'clause_type', 'label': 'Clause Type', 'path': 'clause_type',
                 'search': True, 'viewable': True, 'type': 'code', 'count': True},
                {'key': 'annotated', 'label': 'Annotated', 'path': 'get_thumb', 'viewable': False, 'search': False,
                 'type': 'boolean', 'count': True, 'labels': {0: 'not annotated', 1: 'annotated'}},
                {'key': 'mp_permission', 'label': 'Image availability',
                 'path': 'get_thumb.image.get_media_permission.get_permission_label', 'type': 'code', 'count': True},
                {'key': 'PRIVATE', 'label': 'Private',
                 'path': 'content_xml.is_private', 'type': 'boolean', 'search': True},
            ],
            #                    'select_related': ['content_xml.text_content.item_partitem_part__current_item__repository__place', 'assigned_place', 'assigned_date'],
            'prefetch_related': ['text_content__item_part__historical_items'],
            #                     'filter_order': ['hand_date', 'repo_city', 'repo_place', 'hand_place'],
            #                     #'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'locus', 'hi_date', 'annotations', 'hi_format', 'hi_type', 'thumbnail'],
            #                     #'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'locus', 'hi_date'],
            'sorted_fields': ['repo_city', 'repo_place', 'shelfmark', 'text_type'],
            #                    'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'text_type'],
        },

        {
            'disabled': False,
            'key': 'graphs',
            'label': 'Graph',
            'model': 'digipal.models.Graph',
            'django_filter': {'annotation__isnull': False},
            'fields': [
                {'key': 'url', 'label': 'Address', 'label_col': ' ',
                 'path': 'get_absolute_url', 'type': 'url', 'viewable': True},
                {'key': 'hi_type', 'label': 'Document Type', 'path': 'annotation.image.item_part.historical_item.historical_item_type.name',
                 'type': 'id', 'viewable': True, 'count': True},
                {'key': 'repo_city', 'label': 'Repository City', 'path': 'annotation.image.item_part.current_item.repository.place.name',
                 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                {'key': 'repo_place', 'label': 'Repository', 'path': 'annotation.image.item_part.current_item.repository.human_readable',
                 'path_result': 'annotation.image.item_part.current_item.repository.name', 'count': True, 'search': True, 'viewable': True, 'type': 'title'},
                {'key': 'shelfmark', 'label': 'Shelfmark', 'path': 'annotation.image.item_part.current_item.shelfmark',
                 'search': True, 'viewable': True, 'type': 'code'},
                {'key': 'hand_place', 'label': 'Medieval Place', 'path': 'hand.assigned_place.name',
                 'search': True, 'viewable': True, 'type': 'code', 'count': True},
                {'key': 'hand_label', 'label': 'Hand', 'path': 'hand.label',
                 'search': True, 'viewable': True, 'type': 'title', 'count': True},
                {'key': 'locus', 'label': 'Locus', 'path': 'annotation.image.locus',
                 'search': True, 'viewable': True, 'type': 'code'},
                {'key': 'chartype', 'label': 'Character Type', 'path': 'idiograph.allograph.character.ontograph.ontograph_type.name',
                 'viewable': True, 'type': 'code', 'count': True},
                {'key': 'character_form', 'label': 'Character Form',
                 'path': 'idiograph.allograph.character.form.name', 'viewable': True, 'type': 'code', 'count': True},
                {'key': 'character', 'label': 'Character', 'path': 'idiograph.allograph.character.name',
                 'viewable': True, 'type': 'id', 'count': True},
                {'key': 'allograph', 'label': 'Allograph', 'path': 'idiograph.allograph.human_readable', 'viewable': True,
                 'type': 'id', 'count': True, 'sort_fct': lambda r: str(r.character.ontograph.sort_order)},
                {'key': 'hand_date', 'label': 'Hand Date', 'path': 'hand.assigned_date.date', 'type': 'date',
                 'filter': True, 'viewable': True, 'search': True, 'id': 'hi_date', 'min': 680, 'max': 1200},
                {'key': 'is_described', 'label': 'Described?', 'path': 'graph_components.all.count',
                 'viewable': True, 'type': 'boolean', 'count': True, 'labels': {0: 'not described', 1: 'described'}},
                {'key': 'thumbnail', 'label': 'Thumbnail',
                 'path': 'annotation', 'viewable': True, 'type': 'image'},

                {'key': 'hi_date', 'label': 'MS Date', 'path': 'annotation.image.item_part.historical_item.get_date_sort',
                 'type': 'date', 'filter': True, 'viewable': True, 'search': True, 'id': 'hi_date', 'min': 500, 'max': 1300},

                {'key': 'mp_permission', 'label': 'Availability',
                 'path': 'annotation.image.get_media_permission.get_permission_label', 'type': 'code', 'count': True},

                {'key': 'PRIVATE', 'label': 'Private',
                 'path': 'annotation.image.is_media_private', 'type': 'boolean', 'search': True},

                {'key': 'CONFLATEID', 'label': 'Conflate ID',
                 'path': 'annotation.image.item_part.id', 'type': 'int'},

                #                            {'key': 'full_size', 'label': 'Image', 'path': 'get_media_right_label', 'type': 'boolean', 'count': True, 'search': True},
                #                            {'key': 'hi_format', 'label': 'Format', 'path': 'item_part.historical_item.historical_item_format.name', 'type': 'code', 'viewable': True, 'count': True},
                #                            {'key': 'annotations', 'label_col': 'Ann.', 'label': 'Annotations', 'path': 'annotation_set.all.count', 'type': 'int', 'viewable': True},
                #                            {'key': 'script', 'label': 'Script', 'path': 'idiograph.allograh.script.name', 'viewable': True, 'type': 'code'},
                #{'key': 'hand_script', 'label': 'Script of the Hand', 'label_col': 'Script', 'path': 'hand.script.name', 'viewable': True, 'search': True, 'type': 'code', 'count': True},
            ],
            'select_related': ['annotation__image__item_part__current_item__repository__place',
                               'idiograph__allograph__character__ontograph__ontograph_type',
                               'idiograph__allograph__character__form__name',
                               'hand__assigned_place'
                               ],
            'prefetch_related': ['annotation__image__item_part__historical_items',
                                 'annotation__image__item_part__historical_items__historical_item_format',
                                 'annotation__image__item_part__historical_items__historical_item_type'
                                 ],
            'filter_order': [
                'hand_date', 'chartype', 'character_form', 'character', 'allograph', 'is_described',
                'hand_label', 'hand_place', 'repo_place', 'repo_city'
            ],
            #                     'filter_order': [
            #                                      'hand_date', 'mp_permission', 'is_described', 'repo_city', 'repo_place',
            #                                      'shelfmark', 'hand_place', 'hand_label', 'chartype', 'character_form',
            #                                      'character', 'allograph'
            #                                      ],
            'column_order': ['url', 'repo_city', 'repo_place', 'shelfmark', 'locus', 'hi_date', 'hand_label', 'hand_date', 'allograph', 'thumbnail'],
            #'sorted_fields': ['repo_city', 'repo_place', 'shelfmark', 'locus', 'allograph'],
            'sorted_fields': ['repo_city', 'repo_place', 'shelfmark', 'locus', 'allograph'],
            'views': [
                get_fragment('view_default'),
                {'icon': 'th', 'label': 'Grid View', 'key': 'grid', 'type': 'grid',
                 'template': 'graph_grid', 'page_sizes': [50, 100, 200]},
                {'icon': 'list-alt', 'label': 'Grouped Grid View', 'key': 'ggrid',
                 'type': 'ggrid', 'template': 'graph_grid_grouped', 'page_sizes': [50, 100, 200]},
            ],
        },
    ]
})

graph_sample = deepcopy(FACETED_SEARCH['types'][-1])
graph_sample.update({
                    'disabled': True,
                    'key': 'graph_samples',
                    'label': 'Graph (sample)',
                    'label_plural': 'Graphs (sample)',
                    'django_filter': {'annotation__isnull': False, 'id__lt': 20000},
                    })
FACETED_SEARCH['types'].append(graph_sample)

FACETED_SEARCH['type_keys'] = {}
for t in FACETED_SEARCH['types']:
    FACETED_SEARCH['type_keys'][t['key']] = t


def remove_fields_from_faceted_search(fields, content_type_key=None):
    # Removed a field completely from a content_type in the faceted search.
    # If content_type_key is None, the field is removed from all content types.
    for content_type in FACETED_SEARCH['types']:
        if content_type_key is None or content_type_key == content_type['key']:
            for ft in ['column_order', 'sorted_fields', 'filter_order']:
                if ft in content_type:
                    content_type[ft] = [
                        c for c in content_type[ft] if c not in fields]

            content_type['fields'] = [
                c for c in content_type['fields'] if c['key'] not in fields]


def get_content_type_from_key(key):
    return [t for t in FACETED_SEARCH['types'] if t['key'] == key].pop()


class FacettedType(object):
    '''
        A wrapper around the settings of a faceted search result type.
        Provides convenient methods to get more info or update the settings.

        Usage:

        ft = FacettedType().fromKey('manuscripts')
        print ft.getOption('column_order')
    '''

    def __init__(self, options):
        self.options = options

    def getKey(self):
        return self.options['key']

    @staticmethod
    def getFragment(key, default=None, copy=False):
        ret = FACETED_SEARCH['fragments'].get(key, default)
        if copy:
            ret = deepcopy(ret)
        return ret

    @staticmethod
    def getGlobal(key, default=None, copy=False):
        '''Returns a value at the root of FACETED_SEARCH'''
        ret = FACETED_SEARCH.get(key, default)
        if copy:
            ret = deepcopy(ret)
        return ret

    @staticmethod
    def fromKey(akey):
        ret = None
        for options in FACETED_SEARCH['types']:
            if options['key'] == akey:
                return FacettedType(options)
        return ret

    @staticmethod
    def fromModelName(name):
        ret = None
        for options in FACETED_SEARCH['types']:
            if options['model'].lower().endswith('.%s' % name.lower()):
                return FacettedType(options)
        return ret

    def getModelClass(self):
        path = self.options['model'].split('.')
        ret = __import__('.'.join(path[:-1]))
        for part in path[1:]:
            ret = getattr(ret, part)
        return ret

    @staticmethod
    def getAll():
        return [FacettedType(options) for options in FACETED_SEARCH['types']]

    def addField(self, field_definition=None, after_key=None):
        if field_definition:
            index = 0
            for field in self.getFields():
                if field['key'] == after_key:
                    break
                index += 1
            self.options['fields'].insert(index + 1, field_definition)

    def getField(self, key):
        ret = None
        for field in self.getFields():
            if field['key'] == key:
                ret = field
                break
        return ret

    def getFields(self):
        return self.options['fields']
    fields = property(getFields)

    def getOption(self, key, default=None):
        return self.options.get(key, default)

    @staticmethod
    def getDefaultView(selected=False):
        ret = FacettedType.getFragment('view_default', copy=True)
        ret['selected'] = selected
        return ret

    def getViewsRaw(self):
        '''Returns the views'''
        ret = self.options.get('views', None)
        if ret is None:
            ret = self.options['views'] = []
        return ret

    def getViews(self):
        '''Returns a copy of the views with possibly additional default views'''
        ret = deepcopy(self.getViewsRaw())
        view_keys = [v['key'] for v in ret]

        # add default view
        default_view = self.getDefaultView()
        if default_view['key'] not in view_keys:
            ret.insert(0, default_view)

        # add overview
        overview = self.getFragment('overview', copy=True)
        if overview['key'] not in view_keys:
            ret.append(overview)

        return ret

    def getViewsEnabled(self):
        '''Returns a copy of the views, with default views, but only the enabled ones'''
        return [v for v in self.getViews() if not v.get('disabled', False)]

    def disableView(self, key, enable=False):
        views = self.getViewsRaw()
        view = None
        for v in views:
            if v['key'] == key:
                view = view
                break
        if not view and not enable:
            view = {'key': key}
            views.append(view)
        if view:
            view['disabled'] = not enable

    def getFilterKeys(self):
        ''' Returns a list of fitler field keys in the order they should appear in the filter panel'''
        ret = self.getOption('filter_order', None)
        if not ret:
            ret = [field['key'] for field in self.fields if field.get(
                'count', False) or field.get('filter', False)]
        return ret

    def addFieldsToOption(self, option='filter_order',
                          keys=None, after_key=None):
        for key in keys:
            self.addFieldToOption(option=option, key=key, after_key=after_key)
            after_key = key

    def addFieldToOption(self, option='filter_order',
                         key=None, after_key=None):
        l = self.options.get(option, None)
        if l:
            try:
                index = l.index(after_key) + 1 if after_key else len(l)
                l.insert(index, key)
            except ValueError:
                pass

    @classmethod
    def isFieldAFacet(cls, field):
        '''Is this field displayed as a facet on the faceted search'''
        return field.get('count', False) or field.get('filter', False)

    @classmethod
    def areFieldOptionsShown(cls, field):
        '''Should the field values be retrieved and displayed as facet options?'''
        return cls.isFieldAFacet(field) and not field.get(
            'hide_options', field['type'] in ['date'])

    def setDateRange(self, rng):
        for f in self.fields:
            if f['type'] == 'date':
                f['min'], f['max'] = rng
