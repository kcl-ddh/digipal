from django import http
from django.conf import settings
import re

class HttpsAdminMiddleware(object):
    '''Redirect a request to a non admin paths to http'''
    def process_request(self, request):
        if getattr(settings, 'DEBUG', False):
            print '-' * 80
            from datetime import datetime
            print '%s' % datetime.now()

        return None
        
    def process_response(self, request, response):
        if getattr(settings, 'ADMIN_FORCE_HTTPS', False):
            path = request.get_full_path()
            if request.is_secure() and not re.search(ur'(?i)^/admin(/|$)', path):
                new_url = 'http://%s%s' % (request.get_host(), path)
                response = http.HttpResponseRedirect(new_url)
        return response
    