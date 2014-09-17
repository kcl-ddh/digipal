from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404
import re

def doc_view(request, path):
    template = 'digipal/doc_page.html'
    context = {}
    
    context['doc'] = get_doc_from_path(path)
    
    return render_to_response(template, context, context_instance=RequestContext(request))

def get_doc_from_path(path):
    # find the doc file from the given path
    file_path = get_doc_absolute_path(path)
    
    # read the raw doc
    from digipal.management.commands.utils import readFile
    md = readFile(file_path)
      
    # transform into HTML
    ret = get_doc_from_md(md)
        
    return ret

def get_doc_from_md(md):
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
    ret['content'] = mark_safe(markdown2.markdown(md))
    
    return ret

def get_doc_absolute_path(relative_path):
    path = relative_path
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
