from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
import json
import os
from collections import OrderedDict
from digipal.forms import SearchPageForm
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from mezzanine.conf import settings
from digipal.templatetags import hand_filters
from digipal.models import *

from subprocess import Popen
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required


def get_search_types(request=None):
    from content_type.search_hands import SearchHands
    from content_type.search_manuscripts import SearchManuscripts
    from content_type.search_scribes import SearchScribes
    from content_type.search_graphs import SearchGraphs
    search_hands = SearchHands()
    from digipal.utils import is_model_visible
    ret = [search_model for search_model in [SearchManuscripts(), search_hands, SearchScribes(
    ), SearchGraphs(search_hands)] if is_model_visible(search_model.get_model(), request or True)]

    return ret


def get_search_types_display(content_types):
    ''' returns the content types as a string like this:
        'Hands', 'Scribes' or 'Manuscripts'
    '''
    ret = ''
    for type in content_types:
        if ret:
            if type == content_types[-1]:
                ret += ' and '
            else:
                ret += ', '
        ret += '\'%s\'' % type.label
    return ret


@staff_member_required
@csrf_exempt
def search_index_view(request):
    context = {'indexes': OrderedDict()}

    '''
    todo
    DONE reindex selected indexes in background
    . show when indexer is working
    . lock form (if working)
    . show last time indexer started (if working)
    . ajaxify
    . vue.js?
    '''

    from digipal.views.faceted_search import faceted_search
    from digipal.utils import get_all_files_under
    from datetime import datetime
    from digipal.views.faceted_search.search_indexer import SearchIndexer

    indexer = SearchIndexer()

    content_types = faceted_search.get_types(True)

    # process request
    action = request.POST.get('action', '')
    reindexes = []

    if action == 'cancel':
        context['indexing'] = indexer.read_state()
        if context['indexing']:
            import signal
            pid = context['indexing']['pid']
            # kill process
            try:
                res = os.kill(pid, signal.SIGKILL)
            except OSError, e:
                # Process doesn't exist
                if e.errno == 3:
                    pass
            # reset state
            indexer.clear_state()

    if action == 'reindex':
        for ct in content_types:
            if request.POST.get('select-%s' % ct.key):
                reindexes.append(ct.key)

        if reindexes:
            dputils.call_management_command(
                'dpsearch', 'index_facets', **{'if': ','.join(reindexes)})
            context['indexing'] = indexer.get_state_initial(reindexes)

    if not 'indexing' in context:
        context['indexing'] = indexer.read_state()

    context['running'] = context['indexing'] and context['indexing']['progress'] < 1.0
    now = datetime.now()
    if context['indexing'] and\
            (not context['running'] and ((now - context['indexing']['updated']).total_seconds() > (60 * 10))):
        context['indexing'] = None

    # read the index stats
    for ct in content_types:
        info = {'date': 0, 'size': 0}
        context['indexes'][ct.key] = {
            'object': ct,
            'info': info,
            'indexing': context['indexing']['indexes'].get(ct.key, None) if context['indexing'] else None,
        }

        for afile in get_all_files_under(ct.get_whoosh_index_path(), file_types='f'):
            info['size'] += os.path.getsize(afile)
            info['date'] = max(info['date'], os.path.getmtime(afile))

        info['date'] = datetime.fromtimestamp(info['date'])
        info['size'] = int(info['size'])

    context['title'] = 'Search Indexer'

    template = 'search/search_index.html'
    if request.is_ajax():
        template = 'search/search_index_fragment.html'

    ret = render_to_response(
        template, context, context_instance=RequestContext(request))
    return ret


def catalogue_number_view(request, source='', number=''):
    cns = CatalogueNumber.objects.filter(
        source__label_slug=slugify(source), number_slug=slugify(number))
    if len(list(cns)) == 1:
        # TODO: error management: no hi, no ip, multiple his, mutliple ips,
        # etc.
        ipi = ItemPartItem.objects.filter(
            historical_item=cns[0].historical_item).first()
        ip = ipi.item_part
        from django.shortcuts import redirect
        redirect_url = ip.get_absolute_url()
        return redirect(redirect_url)
    else:
        raise Http404(
            'Catalogue number not found. Source "%s", number "%s".' % (source, number))


def record_view(request, content_type='', objectid='', tabid=''):
    '''The generic view for any type of record: Hand, Scribe, Manuscript'''
    context = {'tabid': tabid}

    template = 'errors/404.html'

    # We need to do a search to show the next and previous record
    # Only when we come from the the search image.
    set_search_results_to_context(
        request, allowed_type=content_type, context=context)

    for type in context['types']:
        if type.key == content_type:

            # Hide if not set as visible in settings.py
            from digipal.utils import request_invisible_model
            request_invisible_model(type.get_model(), request, content_type)

            # Now find templates and populate context
            context['id'] = objectid
            from django.core.exceptions import ObjectDoesNotExist
            try:
                template = type.process_record_view_request(context, request)
                if not template.endswith('.html'):
                    # redirect
                    from django.shortcuts import redirect
                    return redirect(template)
            except ObjectDoesNotExist:
                context['title'] = 'This %s record does not exist' % type.label_singular
                template = 'errors/404.html'
            break

    return render_to_response(template, context, context_instance=RequestContext(request))


def index_view(request, content_type=''):
    context = {}

    types = get_search_types(request)

    # search & sort
    from datetime import datetime
    t0 = datetime.now()
    for type in types:
        if type.key == content_type:
            type.set_index_view_context(context, request)
            break
    t1 = datetime.now()
    # print '%s' % (t1 - t0)

    # pagination
    page_letter = request.GET.get('pl', '').lower()
    context['pages'] = [
        {'label': 'All', 'id': '', 'selected': (not page_letter)}]
    context['selected_page'] = context['pages'][0]
    for i in range(ord('a'), ord('z') + 1):
        page = {'label': ('%s' % chr(i)).upper(), 'id': chr(i), 'selected': (
            chr(i) == page_letter), 'disabled': not(chr(i) in context['active_letters'])}
        context['pages'].append(page)
        if page['selected']:
            context['selected_page'] = page

    template = 'pages/record_index.html'

    return render_to_response(template, context, context_instance=RequestContext(request))


def search_ms_image_view(request):
    '''View for the Browse Image page'''

    hand_filters.chrono('BROWSE:')

    from digipal.utils import request_invisible_model
    request_invisible_model('image', request, 'Image')

    hand_filters.chrono('search:')
    hand_filters.chrono('all():')
    images = Image.objects.all()
    hand_filters.chrono(':all()')

    from digipal.forms import FilterManuscriptsImages

    # Get Buttons
    context = {}

    context['view'] = request.GET.get('view', 'images')

    town_or_city = request.GET.get('town_or_city', '')
    repository = request.GET.get('repository', '')
    date = request.GET.get('date', '')

    set_page_sizes_to_context(request, context, [12, 20, 40, 100])

    # Applying filters
    if town_or_city:
        images = images.filter(
            item_part__current_item__repository__place__name=town_or_city)
    if repository:
        # repo is in two parts: repo place, repo name (e.g. cambridge, corpus christi college)
        # but we also support old style URL which have only the name of the repo
        # if we don't, crawlers like Googlebot could receive a 500 error (see
        # JIRA DIGIPAL-483)
        repo_parts = [p.strip() for p in repository.split(',')]
        if repo_parts:
            images = images.filter(
                item_part__current_item__repository__name=repo_parts[-1])
        if len(repo_parts) > 1:
            images = images.filter(
                item_part__current_item__repository__place__name=repo_parts[0])
    if date:
        images = images.filter(hands__assigned_date__date=date)

    images = images.filter(item_part_id__gt=0)
    # not sufficient, see JIRA #552
    # images = Image.sort_query_set_by_locus(images)

    # images = list(images.order_by('id'))
    # from digipal.utils import natural_sort_key
    # images = sorted(images, key=lambda im: natural_sort_key(im.display_label, True))
    # context['images'] = Image.sort_query_set_by_locus(images.prefetch_related('hands', 'annotation_set'))

    # permission filter
    # OPT: on DigiPal prefetch_related of annotation_set takes 20s and it retrieves all the fields even
    # related to linked tables (allograph, character, etc.)
    # Same with hands which takes around 2/3 s.
    # images = Image.filter_permissions_from_request(images.prefetch_related('hands', 'annotation_set'), request)
    images = Image.filter_permissions_from_request(images, request)

    hand_filters.chrono(':search')

    # count hands
    hand_filters.chrono('hands:')
    from django.db.models import Count
    context['images'] = Image.sort_query_set_by_locus(images.select_related(
        'item_part__current_item__repository__place').annotate(hand_count=Count('hands')))
    hand_filters.chrono('hands:')

    image_search_form = FilterManuscriptsImages(request.GET)
    context['image_search_form'] = image_search_form
    context['query_summary'], context['query_summary_interactive'] = get_query_summary(
        request, '', True, [image_search_form])

    hand_filters.chrono('template:')
    ret = render_to_response('search/search_ms_image.html',
                             context, context_instance=RequestContext(request))
    hand_filters.chrono(':template')

    hand_filters.chrono(':BROWSE')

    return ret


def reroute_to_static_search(request):
    ret = None
    # Rerouting to the blog/news search result page
    scope = request.GET.get('scp', '')
    if scope == 'st':
        from django.shortcuts import redirect
        redirect_url = '/blog/search/?q=%s' % request.GET.get('terms')
        ret = redirect(redirect_url)
    return ret


def search_record_view(request):
    ret = reroute_to_static_search(request)
    if ret:
        return ret

    hand_filters.chrono('SEARCH VIEW:')
    hand_filters.chrono('SEARCH LOGIC:')

    # Backward compatibility.
    # Previously all the record pages would go through this search URL and view
    # and their URL was:
    #     /digipal/search/?id=1&result_type=scribes&basic_search_type=hands&terms=Wulfstan
    # Now we redirect those requests to the record page
    #     /digipal/scribes/1/?basic_search_type=hands&terms=Wulfstan+&result_type=scribes
    qs_id = request.GET.get('id', '')
    qs_result_type = request.GET.get('result_type', '')
    if qs_id and qs_result_type:
        from django.shortcuts import redirect
        # TODO: get digipal from current project name or current URL
        redirect_url = '/%s/%s/%s/?%s' % ('digipal',
                                          qs_result_type, qs_id, request.META['QUERY_STRING'])
        return redirect(redirect_url)

    # backward compatibility:
    # query string param 'name' and 'scribes' have ben renamed to 'scribe'
    request.GET = request.GET.copy()
    request.GET['scribe'] = request.GET.get('scribe', '') or request.GET.get(
        'scribes', '') or request.GET.get('name', '')

    request.GET['ms_date'] = request.GET.get(
        'ms_date', '') or request.GET.get('date', '')
    request.GET['hand_date'] = request.GET.get(
        'hand_date', '') or request.GET.get('date', '')
    request.GET['scribe_date'] = request.GET.get(
        'scribe_date', '') or request.GET.get('date', '')

    request.GET['hand_place'] = request.GET.get(
        'hand_place', '') or request.GET.get('place', '')
    request.GET['scriptorium'] = request.GET.get(
        'scriptorium', '') or request.GET.get('place', '')

    # Actually run the searches
    context = {}

    context['nofollow'] = True

    set_search_results_to_context(
        request, context=context, show_advanced_search_form=True)

    # check if the search was executed or not (e.g. form not submitted or
    # invalid form)
    if context.has_key('results'):
        # Tab Selection Logic =
        #     we pick the tab the user has selected even if it is empty. END
        #     if none, we select the filter/advanced search content type
        #     if none or its result is empty we select the first non empty type
        #     if none we select the first type. END
        result_type = request.GET.get('result_type', '')

        # requested result type does not exist => ignore it
        if result_type not in [type.key for type in context['types']]:
            result_type = ''

        if not result_type:
            first_non_empty_type = None
            for type in context['types']:
                if type.key == context['search_type'] and not type.is_empty:
                    result_type = context['search_type']
                    break
                if not first_non_empty_type and not type.is_empty:
                    first_non_empty_type = type.key
            if not result_type:
                result_type = first_non_empty_type

        result_type = result_type or context['types'][0].key
        context['result_type'] = result_type

        # No result at all?
        for type in context['types']:
            if not type.is_empty:
                context['is_empty'] = False

    from digipal import utils
    context['search_help_url'] = utils.get_cms_url_from_slug(
        getattr(settings, 'SEARCH_HELP_PAGE_SLUG', 'search_help'))

    # Initialise the advanced search forms
    # context['drilldownform'] = GraphSearchForm({'terms': context['terms'] or ''})

    page_options = get_search_page_js_data(
        context['types'], request.GET.get('from_link') in ('true', '1'), request)
    context['expanded_custom_filters'] = page_options['advanced_search_expanded']
    page_options['linked_fields'] = []

    for type in context['types']:
        type.add_field_links(page_options['linked_fields'])

    context['search_page_options_json'] = json.dumps(page_options)
    for custom_filter in page_options['filters']:
        if custom_filter['key'] == context['search_type_defaulted']:
            context['filters_form'] = custom_filter

    from digipal.models import RequestLog
    RequestLog.save_request(request, sum(
        [type.count for type in context['types']]))

    hand_filters.chrono(':SEARCH LOGIC')
    hand_filters.chrono('SEARCH TEMPLATE:')

    ret = render_to_response('search/search_record.html',
                             context, context_instance=RequestContext(request))

    hand_filters.chrono(':SEARCH TEMPLATE')

    hand_filters.chrono(':SEARCH VIEW')

    return ret


def set_page_sizes_to_context(request, context, options=[10, 20, 50, 100]):
    context['page_sizes'] = options
    context['page_size'] = request.GET.get('pgs', '')
    if context['page_size'] and context['page_size'].isdigit():
        context['page_size'] = int(context['page_size'])
    if context['page_size'] not in context['page_sizes']:
        context['page_size'] = context['page_sizes'][0]


def set_search_results_to_context(request, context={}, allowed_type=None, show_advanced_search_form=False):
    ''' Read the information posted through the search form and create the queryset
        for each relevant type of content (e.g. MS, Hand) => context['results']

        If the form was not valid or submitted, context['results'] is left undefined.

        Other context variables used by the search template are also set.
    '''

    # allowed_type: this variable is used to restrict the search to one content type only.
    # This is useful when we display a specific record page and we only
    # have to search for the related content type to show the previous/next links.
    # allowed_type = kwargs.get('allowed_type', None)
    # context = kwargs.get('context', {})

    context['terms'] = ''

    # pagination sizes
    set_page_sizes_to_context(request, context)

    # list of query parameter/form fields which can be changed without
    # triggering a search
    context['submitted'] = False
    non_search_params = ['basic_search_type', 'from_link', 'result_type']
    for param in request.GET:
        if param not in non_search_params and request.GET.get(param):
            context['submitted'] = True

    context['can_edit'] = has_edit_permission(request, Hand)
    context['types'] = get_search_types(request)

    context['annotation_mode'] = request.GET.get('am', '0')

    context['view'] = request.GET.get('view', '')
    for type in context['types']:
        type.set_desired_view(context['view'])
        type.set_page_size(context['page_size'])

    context['search_types_display'] = get_search_types_display(
        context['types'])
    context['is_empty'] = True

    advanced_search_form = SearchPageForm(request.GET)

    advanced_search_form.fields['basic_search_type'].choices = [
        (type.key, type.label) for type in context['types']]

    if show_advanced_search_form:
        context['advanced_search_form'] = advanced_search_form

    if advanced_search_form.is_valid():
        # Read the inputs
        # - term
        term = advanced_search_form.cleaned_data['terms']
        context['terms'] = term or ' '
        context['query_summary'], context['query_summary_interactive'] = get_query_summary(
            request, term, context['submitted'], [type.get_form(request) for type in context['types']])

        # - search type
        context['search_type'] = advanced_search_form.cleaned_data['basic_search_type']

        context['search_type_defaulted'] = context['search_type']
        if not context['search_type_defaulted']:
            if context['types']:
                context['search_type_defaulted'] = context['types'][0].key
            else:
                context['search_type_defaulted'] = '?'

        has_result = False

        if context['submitted']:
            # Create the queryset for each allowed content type.
            # If allowed_types is None, search for each supported content type.
            for type in context['types']:
                if allowed_type in [None, type.key]:
                    hand_filters.chrono('Search %s:' % type.key)
                    context['results'] = type.build_queryset(
                        request, term, not has_result)
                    if type.is_empty == False:
                        has_result = True
                    hand_filters.chrono(':Search %s' % type.key)


def get_query_summary(request, term, submitted, forms):
    # Return two strings that summaries the query
    # The first string is plain text, the second is in HTML and allows the user to remove filters
    # e.g. (u'Catalogue Number: "CLA A.1822", Date: "693"',
    # u'Catalogue Number: "CLA A.1822" <a
    # href="?date=693&amp;s=1&amp;from_link=1&amp;result_type=scribes&amp;basic_search_type=manuscripts"><span
    # class="glyphicon glyphicon-remove"></span></a>, Date: "693" <a
    # href="?index=CLA+A.1822&amp;from_link=1&amp;s=1&amp;result_type=scribes&amp;basic_search_type=manuscripts"><span
    # class="glyphicon glyphicon-remove"></span></a>')
    ret = u''

    query_all = False

    from django.utils.html import strip_tags

    def get_filter_html(val, param, label=''):
        ret = u'<a href="%s">' % update_query_params(
            u'?' + request.META['QUERY_STRING'], '%s=' % param)
        if label:
            ret += u'%s: ' % label
        ret += u'"%s" <span class="glyphicon glyphicon-remove"></span>' % escape(
            val)
        ret += u'</a>'
        return ret

    if submitted:
        from digipal.templatetags.html_escape import update_query_params

        if term.strip():
            ret += get_filter_html(term, 'terms')

        found_params = []
        for form in forms:
            for field_name in form.fields:
                if field_name not in found_params:
                    boundfield = form[field_name]
                    field_label = getattr(boundfield, 'label', '') or getattr(
                        boundfield.field, 'empty_label', '') or (boundfield.field.initial) or field_name.title()
                    value = boundfield.value()
                    if value:
                        if hasattr(boundfield.field, 'choices'):
                            for choice_value, choice_label in boundfield.field.choices:
                                if unicode(value) == unicode(choice_value):

                                    # special case for this clunky dropdown...
                                    # The main issue is that it has multiple options with the same value
                                    # e.g. insular -> a,insular, insular, r, insular
                                    # If the user selects r, insular, the page page reloads and we see 'a, insular'
                                    # here we apply some custom logic to show
                                    # the right value.
                                    if field_name == u'allograph':
                                        parts = choice_label.split(',')
                                        if len(parts) == 2:
                                            char = request.GET.get(
                                                'character', '')
                                            if char:
                                                choice_label = u'%s, %s' % (
                                                    char.strip(), parts[1].strip())

                                    # format the field for the summary
                                    if ret:
                                        ret += ', '
                                    ret += get_filter_html(choice_label,
                                                           field_name, field_label)
                                    found_params.append(field_name)
                                    break

        query_all = not ret.strip()

        if query_all:
            ret = u'All'

    ret = [strip_tags(ret), ret]

    # add clear all button (see JIRA 484)
    if not query_all:
        ret[1] += u'<a class="clear-all" href="?s=1">Clear All <span class="glyphicon glyphicon-remove"></span></a>'

    return tuple(ret)


def get_search_page_js_data(content_types, expanded_search=False, request=None):
    filters = []
    for type in content_types:
        filters.append({
            'html': type.get_form(request).as_ul(),
            'label': type.label,
            'key': type.key,
        })

    ret = {
        'advanced_search_expanded': expanded_search or any([type.is_advanced_search for type in content_types]),
        'filters': filters,
    }

    return ret


def search_graph_view(request):
    # this has been integrated into the main search page
    # see search_record_view()

    # we redirect old addresses to the new main search
    from django.shortcuts import redirect
    # TODO: get digipal from current project name or current URL
    redirect_url = '/digipal/search/?basic_search_type=graphs&from_link=1&result_type=graphs&%s' % (
        request.META['QUERY_STRING'].replace('_select=', '='),)
    return redirect(redirect_url)


def search_suggestions(request):
    from digipal.utils import get_json_response
    from content_type.search_content_type import SearchContentType
    query = request.GET.get('q', '')
    try:
        limit = int(request.GET.get('l'))
    except:
        limit = 8
    suggestions = SearchContentType().get_suggestions(query, limit)
    return get_json_response(suggestions)
