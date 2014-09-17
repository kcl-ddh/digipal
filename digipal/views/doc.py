from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404
import re

def doc_view(request, path):
    template = 'digipal/doc_page.html'
    context = {}
    
    context['doc'] = get_doc_from_path(path, request)
    
    return render_to_response(template, context, context_instance=RequestContext(request))

def get_doc_from_path(path, request):
    # find the doc file from the given path
    file_path = get_doc_absolute_path(path)
    
    # read the raw doc
    from digipal.management.commands.utils import readFile
    md = readFile(file_path)
      
    # transform into HTML
    ret = get_doc_from_md(md, request)
        
    return ret

def get_doc_from_md(md, request):
    '''Returns the doc info structure from a mark down text (md)'''
    ret = {}
    
    # get the first main title
    for i in range(1, 4):
        pattern = ur'(?musi)^%s\s+(.*?)$' % ('#' * i)
        m = re.search(pattern, md)
        if m:
            ret['title'] = m.group(1)
            break
    
    # convert the document to HTML
    import markdown2
    from django.utils.safestring import mark_safe
    
    md = preprocess_markdown(md, request)
    
    html = markdown2.markdown(md)

    html = postprocess_markdown(html, request)
    
    ret['content'] = mark_safe(html)
    
    return ret

def postprocess_markdown(html, request):
    # convert 'code' into 'pre'
    ret = html
    ret = re.sub('<code>', '<pre>', ret)
    ret = re.sub('</code>', '</pre>', ret)
    
    # convert links to static files
    # <img href="/digipal/static/doc/april-boat.jpg?raw=true"/>
    # => <img href="/static/doc/april-boat.jpg?raw=true"/>
    # We have to make sure the URL is relative to this site (i.e. starts with /)
    # We assume that doc images are stored in a 'static' folder in the repo.
    # We also assume that the web path to static files starts with 'static'.
    ret = re.sub(ur'(href|src)="/[^"]*(/static/[^"]*)"', ur'\1="\2"', ret)
    
    return ret


def preprocess_markdown(md, request):
    ret = md
    
    # convert link to another .md file 
    # e.g. [See the other test document](test2.md)
    # => [See the other test document](test2)
    link_prefix = ''
    request_path = request.META['PATH_INFO']
    if request_path[-1] == '/':
        link_prefix = '../'
    
    ret = re.sub(ur'\]\(([^)]+).md\)', ur'](%s\1)' % link_prefix, ret)
    
    return ret

def get_doc_absolute_path(relative_path):
    path = relative_path.strip('/')
    parts = path.split('/')

    if len(parts) <= 1:
        raise Http404('Documentation page not found (path not specified)')
        
    import os

    app_name = parts[0]
    search_path = '/'.join(parts[1:])
    
    module = None
    
    from django.utils import importlib
    try:
        module = importlib.import_module(app_name.lower())
    except ImportError:
        raise Http404('Documentation page not found (no app with name "%s")' % app_name)

    file_path = os.path.join(unicode(module.__path__[0]), 'doc', unicode(search_path + '.md'))
    
    if not os.path.exists(file_path):
        raise Http404('Documentation page not found (no doc with path "%s")' % path)
    
    return file_path
