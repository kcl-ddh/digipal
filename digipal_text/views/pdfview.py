# pip install reportlab xhtml2pdf pypdf
import cStringIO as StringIO
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from cgi import escape
from django.template import loader, RequestContext
import re

def render_to_pdf(request, template_src, context_dict):
    template = get_template(template_src)
    context = Context(context_dict)
    #html  = template.render(context)
    context_instance = RequestContext(request)
    html = loader.render_to_string(template_src, context_dict, context_instance=context_instance)
    
    html = includeCss(html)

    result = StringIO.StringIO()

    #pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("ISO-8859-1")), result)
    pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("UTF-8")), result, encoding='UTF-8')
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))

def includeCss(html):
    ret = html
    
    # PDF rconversion doesn't support references to CSS files
    # => embed the style sheet directly within the response
    # <link rel="stylesheet" href="/static/digipal_text/viewer/viewer.css"/>
    
    def rep(match):
        ret = match.group(0)
        
        web_path = match.group(1)
        content = read_static_file(web_path)
        
        #print web_path, len(content)
        
        ret = ur'<style type="text/css">%s</style>' % content
        
        return ret
    
    ret = re.sub(ur'<link\s[^>]*\shref="(.*?)"[^>]*/?>', rep, ret)
    
    #print repr(ret)
    
    #exit()
    
    return ret

def read_static_file(web_path):
    from mezzanine.conf import settings
    from django.conf.urls.static import static
    
    file_path = '%s/%s' % (settings.STATIC_ROOT, re.sub('^'+re.escape(settings.STATIC_URL), '', web_path))
    file_path = re.sub(ur'\?.*$', '', file_path)
    
    from digipal.utils import read_file
    ret = read_file(file_path)
    
    # src: url('../junicode/Junicode.eot?#iefix') format('embedded-opentype'),  url('../junicode/Junicode.woff') format('woff'), url('../junicode/Junicode.ttf')  format('truetype'), url('../junicode/Junicode.svg#Junicode') format('svg');
    #ret = re.sub(ur"(?musi)src:[^;]*junicode*[^;]*;", ur"src: url('/static/digipal_text/junicode/Junicode.ttf');", ret)
    #ret = re.sub(ur"(?musi)src:[^;]*junicode*[^;]*;", ur"", ret)
    ret = re.sub(ur"(?musi)@font-face\s*{[^}]*}", ur"", ret)

    return ret

    
    