from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.utils import simplejson
from digipal.models import *
from digipal.forms import SearchPageForm

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from digipal.templatetags import hand_filters

import logging
dplog = logging.getLogger('digipal_debugger')

def get_search_types():
    from content_type.search_hands import SearchHands
    from content_type.search_manuscripts import SearchManuscripts
    from content_type.search_scribes import SearchScribes
    ret = [SearchManuscripts(), SearchHands(), SearchScribes()]

    from content_type.search_graphs import SearchGraphs
    ret.append(SearchGraphs())
    
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

def record_view(request, content_type='', objectid='', tabid=''):
    context = {'tabid': tabid}
    
    # We need to do a search to show the next and previous record
    # Only when we come from the the search image.
    set_search_results_to_context(request, allowed_type=content_type, context=context)
    
    for type in context['types']:
        if type.key == content_type:
            context['id'] = objectid
            from django.core.exceptions import ObjectDoesNotExist
            try:
                type.set_record_view_context(context, request)
                type.set_record_view_pagination_context(context, request)
                template = 'pages/record_' + content_type +'.html'
            except ObjectDoesNotExist:
                context['title'] = 'This %s record does not exist' % type.label_singular
                template = 'errors/404.html'
            break
    
    return render_to_response(template, context, context_instance=RequestContext(request))

def index_view(request, content_type=''):
    context = {}
    
    types = get_search_types()
    
    # search & sort
    from datetime import datetime
    t0 = datetime.now()
    for type in types:
        if type.key == content_type:
            type.set_index_view_context(context, request)
            break
    t1 = datetime.now()
    #print '%s' % (t1 - t0)
    
    # pagination
    page_letter = request.GET.get('pl', '').lower()
    context['pages'] = [{'label': 'All', 'id': '', 'selected': (not page_letter)}]
    context['selected_page'] = context['pages'][0]
    for i in range(ord('a'), ord('z') + 1):
        page = {'label': ('%s' % chr(i)).upper(), 'id': chr(i), 'selected': (chr(i) == page_letter), 'disabled': not(chr(i) in context['active_letters'])}
        context['pages'].append(page)
        if page['selected']:
            context['selected_page'] = page
    
    template = 'pages/record_index.html'
    
    return render_to_response(template, context, context_instance=RequestContext(request))

def search_ms_image_view(request):
    images = Image.objects.all()
    
    from digipal.forms import FilterManuscriptsImages

    # Get Buttons
    context = {}

    context['view'] = request.GET.get('view', 'images')

    town_or_city = request.GET.get('town_or_city', '')
    repository = request.GET.get('repository', '')
    date = request.GET.get('date', '')

    # Applying filters
    if town_or_city:
        images = images.filter(item_part__current_item__repository__place__name = town_or_city)
    if repository:
        repository_place = repository.split(',')[0]
        repository_name = repository.split(', ')[1]
        images = images.filter(item_part__current_item__repository__name=repository_name,item_part__current_item__repository__place__name=repository_place)
    if date:
        images = images.filter(hands__assigned_date__date = date)

    images = images.filter(item_part_id__gt = 0)
    images = Image.sort_query_set_by_locus(images)

    context['images'] = images

    image_search_form = FilterManuscriptsImages(request.GET)
    context['image_search_form'] = image_search_form
    context['query_summary'], context['query_summary_interactive'] = get_query_summary(request, '', True, [image_search_form])

    return render_to_response('search/search_ms_image.html', context, context_instance=RequestContext(request))

def search_record_view(request):
    # Backward compatibility.
    #
    # Previously all the record pages would go through this search URL and view
    # and their URL was: 
    #     /digipal/search/?id=1&result_type=scribes&basic_search_type=hands&terms=Wulfstan
    # Now we redirect those requests to the record page
    #     /digipal/scribes/1/?basic_search_type=hands&terms=Wulfstan+&result_type=scribes
    
    scope =  request.GET.get('scp', '')
    if scope == 'st':
        from django.shortcuts import redirect
        redirect_url = '/blog/search/?q=%s' % request.GET.get('terms')
        return redirect(redirect_url)
    
    hand_filters.chrono('SEARCH VIEW:')
    hand_filters.chrono('SEARCH LOGIC:')
    
    qs_id = request.GET.get('id', '')
    qs_result_type = request.GET.get('result_type', '')
    if qs_id and qs_result_type:
        from django.shortcuts import redirect
        # TODO: get digipal from current project name or current URL
        redirect_url = '/%s/%s/%s/?%s' % ('digipal', qs_result_type, qs_id, request.META['QUERY_STRING'])
        return redirect(redirect_url)
    
    # Actually run the searches
    context = {}

    set_search_results_to_context(request, context=context, show_advanced_search_form=True)

    # check if the search was executed or not (e.g. form not submitted or invalid form)
    if context.has_key('results'):
        # Tab Selection Logic =
        #     we pick the tab the user has selected even if it is empty. END
        #     if none, we select a the advanced search content type
        #     if none or its result is empty we select the first non empty type 
        #     if none we select the first type. END
        result_type = request.GET.get('result_type', '')

        if not result_type:
            first_non_empty_type = None
            for type in context['types']:
                if type.key == context['search_type'] and not type.is_empty:
                    result_type = context['search_type']
                    break
                if not first_non_empty_type and not type.is_empty:
                    first_non_empty_type = type.key
            if not result_type: result_type = first_non_empty_type
        
        result_type = result_type or context['types'][0].key
        context['result_type'] = result_type
        
        # No result at all?
        for type in context['types']:
            if not type.is_empty:
                context['is_empty'] = False

    context['search_help_url'] = get_cms_url_from_slug(getattr(settings, 'SEARCH_HELP_PAGE_SLUG', 'search_help'))

    # Initialise the advanced search forms 
    from django.utils import simplejson
    #context['drilldownform'] = GraphSearchForm({'terms': context['terms'] or ''})
    
    custom_filters = get_search_page_js_data(context['types'], request.GET.get('from_link') in ('true', '1'), request)
    context['expanded_custom_filters'] = custom_filters['advanced_search_expanded'] 
    context['search_page_options_json'] = simplejson.dumps(custom_filters)
    for custom_filter in custom_filters['filters']:
        if custom_filter['key'] == context['search_type_defaulted']:
            context['filters_form'] = custom_filter
    
    from digipal.models import RequestLog
    RequestLog.save_request(request, sum([type.count for type in context['types']]))

    hand_filters.chrono(':SEARCH LOGIC')
    hand_filters.chrono('SEARCH TEMPLATE:')
    
    ret = render_to_response('search/search_record.html', context, context_instance=RequestContext(request))

    hand_filters.chrono(':SEARCH TEMPLATE')
    
    hand_filters.chrono(':SEARCH VIEW')

    return ret

def set_search_results_to_context(request, context={}, allowed_type=None, show_advanced_search_form=False):
    ''' Read the information posted through the search form and create the queryset
        for each relevant type of content (e.g. MS, Hand) => context['results']
        
        If the form was not valid or submitted, context['results'] is left undefined.
        
        Other context variables used by the search template are also set.        
    '''    
    
    # allowed_type: this variable is used to restrict the search to one content type only.
    # This is useful when we display a specific record page and we only
    # have to search for the related content type to show the previous/next links.
    #allowed_type = kwargs.get('allowed_type', None)
    #context = kwargs.get('context', {})
    
    context['terms'] = ''

    # pagination sizes
    context['page_sizes'] = [10, 20, 50, 100]
    context['page_size'] = request.GET.get('pgs', '')
    if context['page_size'] and context['page_size'].isdigit():
        context['page_size'] = int(context['page_size'])
    if context['page_size'] not in context['page_sizes']:
        context['page_size'] = context['page_sizes'][0]  
        
    # list of query parameter/form fields which can be changed without triggering a search 
    context['submitted'] = False
    non_search_params = ['basic_search_type', 'from_link', 'result_type']
    for param in request.GET:     
        if param not in non_search_params and request.GET.get(param):
            context['submitted'] = True
    
    context['can_edit'] = has_edit_permission(request, Hand)
    context['types'] = get_search_types()
    
    context['view'] = request.GET.get('view', '')
    for type in context['types']:
        type.set_desired_view(context['view'])
        type.set_page_size(context['page_size'])
    
    context['search_types_display'] = get_search_types_display(context['types'])
    context['is_empty'] = True

    advanced_search_form = SearchPageForm(request.GET)
    
    advanced_search_form.fields['basic_search_type'].choices = [(type.key, type.label) for type in context['types']]
    
    if show_advanced_search_form:
        context['advanced_search_form'] = advanced_search_form

    if advanced_search_form.is_valid():
        # Read the inputs
        # - term
        term = advanced_search_form.cleaned_data['terms']
        context['terms'] = term or ' '
        context['query_summary'], context['query_summary_interactive'] = get_query_summary(request, term, context['submitted'], [type.get_form(request) for type in context['types']])
        
        # - search type
        context['search_type'] = advanced_search_form.cleaned_data['basic_search_type']
        context['search_type_defaulted'] = context['search_type'] or context['types'][0].key
        
        has_result = False
        
        if context['submitted']:
            # Create the queryset for each allowed content type.
            # If allowed_types is None, search for each supported content type.
            for type in context['types']:
                if allowed_type in [None, type.key]:
                    hand_filters.chrono('Search %s:' % type.key)
                    context['results'] = type.build_queryset(request, term, not has_result)
                    if type.is_empty == False:
                        has_result = True
                    hand_filters.chrono(':Search %s' % type.key)

def get_query_summary(request, term, submitted, forms):
    # Return two strings that summaries the query
    # The first string is plain text, the second is in HTML and allows the user to remove filters 
    # e.g. (u'Catalogue Number: "CLA A.1822", Date: "693"', 
    # u'Catalogue Number: "CLA A.1822" <a href="?date=693&amp;s=1&amp;from_link=1&amp;result_type=scribes&amp;basic_search_type=manuscripts"><span class="glyphicon glyphicon-remove"></span></a>, Date: "693" <a href="?index=CLA+A.1822&amp;from_link=1&amp;s=1&amp;result_type=scribes&amp;basic_search_type=manuscripts"><span class="glyphicon glyphicon-remove"></span></a>')
    ret = u''
    
    from django.utils.html import conditional_escape, escape, strip_tags
    
    def get_filter_html(val, param, label=''):
        ret = u''
        if label:
            ret += u'%s: ' % label
        ret += u'"%s" <a href="%s"><span class="glyphicon glyphicon-remove"></span></a>' % (escape(val), update_query_params(u'?'+request.META['QUERY_STRING'], '%s=' % param))
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
                    field_label = getattr(boundfield, 'label', '') or getattr(boundfield.field, 'empty_label', '') or (boundfield.field.initial) or field_name.title()
                    value = boundfield.value()
                    if value:
                        for choice_value, choice_label in boundfield.field.choices:
                            if unicode(value) == unicode(choice_value):
                                if ret:
                                    ret += ', '
                                ret += get_filter_html(choice_label, field_name, field_label)
                                found_params.append(field_name)
                                break
                
        
        if not ret.strip():
            ret = 'All'
            
    return strip_tags(ret), ret

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
    };
    
    return ret

def get_cms_url_from_slug(slug):
    from mezzanine.pages.models import Page as MPage 
    for page in MPage.objects.filter(slug__iendswith='how-to-use-digipal'):
        return page.get_absolute_url()
    return u'/%s' % slug

def search_graph_view(request):
    # this has been integrated into the main search page
    # see search_record_view()
    
    # we redirect old addresses to the new main search
    from django.shortcuts import redirect
    # TODO: get digipal from current project name or current URL
    redirect_url = '/digipal/search/?basic_search_type=graphs&from_link=1&result_type=graphs&%s' % (request.META['QUERY_STRING'].replace('_select=', '='),)
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
