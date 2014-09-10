from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape, escape
from django.utils.safestring import mark_safe
import re

register = Library()

@stringfilter
def spacify(value, autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    return mark_safe(re.sub('\s', '%20', esc(value)))
spacify.needs_autoescape = True
register.filter(spacify)

@register.filter(is_safe=True)
@stringfilter
def anchorify(value):
    """
    Like slugify() but preserves the unicode chars
    The problem with slugify is that it will return an empty string for
    a single special char, or identical slugs for strings where only one
    special char varies.
    """
    #value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = re.sub(ur'(?u)[^\w\s-]', u'', value).strip()
    return mark_safe(re.sub(u'[-\s]+', u'-', value))

@register.filter(is_safe=True)
def update_query_params(content, updates):
    ''' The query strings in the content are updated by the filter.
        In case of conflict, the parameters in the filter always win.
    '''
    return update_query_params_internal(content, updates)

@register.filter(is_safe=True)
def add_query_params(content, updates):
    ''' The query strings in the content are updated by the filter.
        In case of conflict, the parameters in the content always win.
    '''
    return update_query_params_internal(content, updates, True)

def update_query_params_internal(content, updates, url_wins=False):
    '''
        Update the query strings found in an HTML fragment.

        See update_query_string()

        E.g.

        >> update_query_string('href="http://www.mysite.com/path/?k1=v1&k2=v2" href="/home"', 'k2=&k5=v5')
        'href="http://www.mysite.com/path/?k1=v1&k5=v5" href="/home?k5=v5"'

    '''
    if len(content.strip()) == 0: return content

    # find all the URLs in content
    template = ur'%s'
    matches = []
    if '"' in content or "'" in content:
        template = ur'href="%s"'
        # we assume the content is HTML
        for m in re.finditer(ur'(?:src|href)\s*=\s*(?:"([^"]*?)"|\'([^\']*?)\')', content):
            matches.append(m)
    else:
        # we assume the content is a single URL
        m = re.search(ur'^(.*)$', content)
        if m:
            matches.append(m)

    from digipal.utils import update_query_string
    for m in matches[::-1]:
        url = max(m.groups())
        new_url = update_query_string(url, updates, url_wins)
        content = content[0:m.start()] + (template % new_url) + content[m.end():]
    
    return content

@register.filter
def plural(value, count=2):
    from digipal.utils import plural
    return plural(value, count)

@register.filter
def tag_phrase_terms(value, phrase=''):
    '''Wrap all occurrences of the terms of [phrase] found in value with a <span class="found-term">.'''
    from digipal.utils import get_regexp_from_terms, get_tokens_from_phrase, remove_combining_marks, remove_accents

    # not nice but we have to do this for the matching below to work
    # we loose *some* the accents, e.g. u'r\u0305'
    value = remove_combining_marks(value)
    value_no_accent = remove_accents(value)
    
    terms = get_tokens_from_phrase(remove_accents(phrase))
    
    if terms:
        # Surround the occurrences of those terms in the value with a span (class="found-term")
        # TODO: this should really be done by Whoosh instead of manually here to deal properly with special cases.
        # e.g. 'G*' should highlight g and the rest of the word
        # Here we have a simple implementation that look for exact and complete matches only.
        # TODO: other issue is highlight of non field values, e.g. (G.) added at the end each description
        #         or headings.
        for re_term in get_regexp_from_terms(terms, True):
            #value = re.sub(ur'(?iu)(>[^<]*)('+re_term+ur')', ur'\1<span class="found-term">\2</span>', u'>'+value)[1:]
            pos = 1
            pattern = re.compile(ur'(?iu)(>[^<]*?)('+re_term+ur')')
            #print re_term
            while True:
                #print value_no_accent, pos
                # pos-1 because we want to include the last > we've inserted in the previous loop.
                # without this we might miss occurrences
                m = pattern.search(value_no_accent, pos - 1)
                #print m
                if m:
                    replacement = u'%s<span class="found-term">%s</span>' % (value[m.start(1):m.end(1)], value[m.start(2):m.end(2)])
                    
                    value = value[:m.start(0)] + replacement + value[m.end(0):]

                    replacement = u'%s<span class="found-term">%s</span>' % (value_no_accent[m.start(1):m.end(1)], value_no_accent[m.start(2):m.end(2)])
                    value_no_accent = value_no_accent[:m.start(0)] + replacement + value_no_accent[m.end(0):]
                    
                    pos = m.start(0) + len(replacement)
                else:
                    break

    return value

@register.assignment_tag
def get_records_from_ids(search_type, recordids):
    '''
        Prepare the records before they are displayed on the search page

        Usage:
            {% prepare_search_result search_type recordids %}
    '''
    return search_type.get_records_from_ids(recordids)

@register.assignment_tag
def reset_recordids():
    '''
        Reset a variable to []

        Use this before autopaginate, e.g.

        {% reset_recordids as recordids %}
        {% autopaginate type.queryset 9 as recordids %}

        There is a bug in autopaginate. It won't reset recordids if we ask
        for an empty page. Without this the result will try to show record
        ids the previous tab.
    '''
    return []

@register.simple_tag
def iip_img_a(image, *args, **kwargs):
    '''
        Usage {% iip_img_a IMAGE [width=W] [height=H] [cls=HTML_CLASS] [lazy=0|1] [padding=0] %}

        Render a <a href=""><img src="" /></a> element with the url referenced
        by the iipimage field.
        width and height are optional. See IIP Image for the way they
        are treated.
    '''
    return mark_safe(ur'<a href="%s&amp;RST=*&amp;QLT=100&amp;CVT=JPEG">%s</a>' % (escape(image.iipimage.full_base_url.replace('\\', '/')), iip_img(image, *args, **kwargs)))

@register.simple_tag
def iip_img(image_or_iipfield, *args, **kwargs):
    '''
        Usage {% iip_img IIPIMAGE_FIELD [width=W] [height=H] [cls=HTML_CLASS] [lazy=0|1] [padding=0] %}

        Render a <img src="" /> element with the url referenced by the
        iipimage field.
        width and height are optional. See IIP Image for the way they
        are treated.
        If lazy is True the image will be loaded only when visible in
        the browser.
    '''
    ret = u''
    if image_or_iipfield is None:
        return ret

    image = None
    iipfield = image_or_iipfield
    if hasattr(image_or_iipfield, 'iipimage'):
        image = image_or_iipfield
        iipfield = image.iipimage
    
    if image:
        kwargs['alt'] = u'%s' % image
        # When we get height = 100 we calculate the width.
        # And vice-versa
        ds = ['width', 'height']
        vs = [kwargs.get(d, None) for d in ds]
        if any(vs):
            dims = image.dimensions()
            if min(dims) > 0:
                for i in [0, 1]:
                    if vs[i] is None:
                        kwargs[ds[i]] = int(float(vs[1-i]) / float(dims[1-i]) * float(dims[i]))
    
        ret = img(iip_url(iipfield, *args, **kwargs), *args, **kwargs)
            
    return ret

@register.simple_tag
def annotation_img(annotation, *args, **kwargs):
    '''
        Usage {% annotation_img ANNOTATION [width=W] [height=H] [cls=HTML_CLASS] [lazy=0|1] [padding=0] %}

        See iip_img() for more information

        fixlen: fix the maximum length of the thumbnail
    '''
    
    ret = u''
    if annotation:
        info = annotation.get_cutout_url_info(fixlen=kwargs.get('fixlen', None))
        #dims = annotation.image.get_region_dimensions(url)
        #kwargs = {'a_data-info': '%s x %s' % (dims[0], dims[1])}
        if info['url']:
            ret = img(info['url'], alt=annotation.graph, rotation=annotation.rotation, holes=annotation.get_holes(), 
                        width=info['dims'][0], height=info['dims'][1], frame_width=info['frame_dims'][0], 
                        frame_height=info['frame_dims'][1], *args, **kwargs)
    return ret

@register.simple_tag
def img(src, *args, **kwargs):
    '''
        Returns <span class="img-frame"><img src="" alt=""></span>.
        The span is a bounding frame around the image. It also serves as 
        mask as the <img> can be bigger than the frame.
        
        XML special chars in the attributes are encoded with &. 
        
        src is the URL of the image to display.
        
        recognised arguments (kwargs):
            alt => alt
            cls => class
            lazy = 0|1 to load the image lazily
            a_X => converted into attribute X
            rotation=float => converted to a CSS rotation in the inline style
            width, height
            padding: nb of pixels between the frame and the image on each side (default = 0)
            holes: {ANNOTATIONID: [offx, offy, lengthx, lengthy], ...}
    '''
    more = ''
    style = ''
    
    #print kwargs 

    if 'alt' in kwargs:
        more += ur' alt="%s" ' % escape(kwargs['alt'])

    for k, v in kwargs.iteritems():
        if k.startswith('a_'):
            more += ur' %s="%s" ' % (k[2:].replace('_', '-'), escape(v))

    if 'cls' in kwargs:
        more += ur' class="%s" ' % escape(kwargs['cls'])
    
    if 'rotation' in kwargs:
        rotation = float(kwargs['rotation'])
        ##style += ';position:relative;max-width:none;'
        if rotation > 0.0 or kwargs.get('force_rotation', False):
            style += ur';transform:rotate(%(r)sdeg); -ms-transform:rotate(%(r)sdeg); -webkit-transform:rotate(%(r)sdeg);' % {'r': rotation}

    if kwargs.get('lazy', False):
        more += ur' data-lazy-img-src="%s" ' % escape(src)
        
        # a serialised white dot GIF image 
        #src = ur'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
        # TODO: don't hard-code the path!
        src = ur'/static/digipal/images/blank.gif'

        # default dimensions
        if 0:
            size = {'width': kwargs.get('width', -1), 'height': kwargs.get('height', -1)}
            for d in size:
                s = size[d]
                if s == -1:
                    s = max(size.values())
                if s == -1:
                    s = 1
                more += ' %s="%s" ' % (d, s)

    frame_css = u''
    padding = int(kwargs.get('padding', '0'))
    for a in ['height', 'width']:
        vs = []
        if a in kwargs:
            vs.append(int(kwargs.get(a)))
            #more += ur' %s="%s" ' % (a, vs[-1])
            style += ';%s:%dpx;' % (a, vs[-1])
        if 'frame_'+a in kwargs:
            vs.append(int(kwargs.get('frame_'+a)))
            frame_css += u';%s:%spx;' % (a, vs[-1] + padding * 2)
        if len(vs) == 2:
            p = 'top'
            if a == 'width':
                p = 'left'
            v = (vs[0]-vs[1])/2
            if v:
                style += ';%s:-%dpx;' % (p, (vs[0]-vs[1])/2)
    
    if style:
        style = ' style="%s" ' % style
    
    ret = ur'<img src="%s" %s %s/>' % (escape(src), more, style)
    
    holes_html = u''
    frame_size = [kwargs.get('frame_width', 0), kwargs.get('frame_height', 0)]
    if all(frame_size):
        for hole in kwargs.get('holes', {}).values():
            # [offx, offy, lengthx, lengthy]
            holes_html += ur'<span class="hole" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;"></span>' % (hole[0] * frame_size[0], hole[1] * frame_size[1], hole[2] * frame_size[0], hole[3] * frame_size[1])
    
    if frame_css:
        frame_css = ' style="%s" ' % frame_css
            
    ret = ur'<span class="img-frame" %s>%s%s</span>' % (frame_css, holes_html, ret)
    
    return mark_safe(ret)

@register.simple_tag
def iip_url(iipfield, *args, **kwargs):
    '''
        Usage {% iip_url IIPIMAGE_FIELD [width=W] [height=H] %}

        Render a url referenced by the iipimage field.
        width and height are optional. See IIP Image for the way they
        are treated.
    '''
    return mark_safe(iipfield.thumbnail_url(kwargs.get('height', None), kwargs.get('width', None)).replace('\\', '/'))

def escapenewline(value):
    """
    Adds a slash before any newline. Useful for loading a multi-line html chunk
    into a Javascript variable.
    """
    return value.replace('\n', '\\\n')
escapenewline.is_safe = True
escapenewline = stringfilter(escapenewline)
register.filter('escapenewline', escapenewline)

@register.inclusion_tag('pagination/pagination_with_size.html', takes_context=True)
def dp_pagination_with_size_for(context, current_page):
    ret = {}
    # JIRA 617
    if current_page:
        ret = dp_pagination_for(context, current_page)
    ret['page_sizes'] = context.get('page_sizes', [10, 20])
    ret['page_size'] = context.get('page_size', 10)
    ret['request'] = context.get('request', None)
    return ret

@register.inclusion_tag('pagination/pagination.html', takes_context=True)
def dp_pagination_for(context, current_page):
    ''' Replacement for mezzanine template tag: pagination_for.
        It takes the same inputs but adapts them to use the django-pagination 
        template we use everywhere else.
        
        current_page = instance of 'django.core.paginator.Page'
    '''    
    # JIRA 617
    context['paginator'] = current_page.paginator if current_page else None 
    context['page_obj'] = current_page
    
    from pagination.templatetags.pagination_tags import paginate
    ret = paginate(context, window=3)
    
    return ret

@register.simple_tag
def render_mezzanine_page(page_title, *args, **kwargs):
    '''
        Usage: {% render_mezzanine_page 'TITLE' %}
        
        Returns the content of the Mezzanine page with title TITLE.
        The output is a string already marked as safe.
    '''
    ret = ''
    from mezzanine.pages.models import Page
    pages = Page.objects.filter(title=page_title)
    if pages.count():
        page = pages[0]
        rtp = page.get_content_model()
        if rtp:
            ret = rtp.content
    return ret

@register.simple_tag
def image_icon(count, message, url, template_type=None, request=None):
    '''Return the HTML for showing an image icon with a count as a link to another page
        count is the number of images
        message is the message to show in the tooltip (e.g. 'COUNT image')

        e.g.
        {% image_icon hand.images.count "COUNT image with this hand" hand.get_absolute_url|add:"pages" template_type request %}
        
        TODO: deal with no request, template type and url
    '''
    
    ret = u''
    
    if count:
        m = re.match(ur'(.*)(COUNT)(\s+)(\w*)(.*)', message)
        if m:
            message = ur'%s%s%s%s%s' % (m.group(1), count, m.group(3), plural(m.group(4), count), m.group(5))
        ret = u'''<span class="result-image-count">
                    (<a data-toggle="tooltip" title="%s" href="%s">%s&nbsp;<i class="fa fa-picture-o"></i></a>)
                  </span>''' % (message, add_query_params(u'%s?result_type=%s' % (url, template_type), request.META['QUERY_STRING']), count)
        
    return mark_safe(ret)

@register.simple_tag
def mezzanine_page_active(request, page):
    '''
        Returns 'active' if the provided Mezzanine <page> 
        is one of its children is in the current path.
        
        This can be used in a template to set active in the class attribute. 
    '''
    ret = False
    
    cs = list(page.children.all())
    cs.append(page)
    path = request.path.strip('/')
    
    for p in cs:
        page_path = re.sub(ur'\?.*$', ur'', p.get_absolute_url()).strip('/')
        if page_path in path:
            ret = True
    
    return 'active' if ret else ''

@register.simple_tag
def record_field(content_type, record, field):
    '''
        {% record_field object field %}
    '''
    return content_type.get_record_field_html(record, field)
