from django.shortcuts import render_to_response
from django.template import RequestContext
from mezzanine.conf import settings

def robots_view(request):
    from digipal.management.commands.sitemap import Command
    context = {}
    import os
    if os.path.exists(Command.get_sitemap_path(file_path=True)):
        context['sitemap_url'] = Command.get_sitemap_path(request=request)
    
    context['debug'] = settings.DEBUG
    #context['debug'] = False
    
    return render_to_response('robots.txt', context, context_instance=RequestContext(request), content_type='text/plain')
