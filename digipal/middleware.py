from django import http
from django.conf import settings
import re

# TODO: log the perfs to a file instead of printing them out
import logging
dplog = logging.getLogger('digipal_debugger')

def are_perf_info_enabled():
    return getattr(settings, 'DEBUG', False) and getattr(settings, 'DEBUG_PERFORMANCE', False)

class HttpsAdminMiddleware(object):
    def process_request(self, request):
        from datetime import datetime
        request.start_time = datetime.now()
        
        if are_perf_info_enabled():
            from datetime import datetime
            self.debug_message('START REQUEST' + '-' * 60)
            self.debug_message('%s' % datetime.now())

        return None
        
    def process_response(self, request, response):
        '''Redirect a request to a non admin paths to http'''
        if getattr(settings, 'ADMIN_FORCE_HTTPS', False):
            path = request.get_full_path()
            if request.is_secure() and not re.search(ur'(?i)^/admin(/|$)', path):
                new_url = 'http://%s%s' % (request.get_host(), path)
                response = http.HttpResponseRedirect(new_url)
        
        if are_perf_info_enabled():
            from datetime import datetime
            request.stop_time = datetime.now()
            self.debug_message('%s (%s)' % (request.path, request.stop_time - request.start_time))
            self.debug_message('END RESPONSE' + '-' * 60)
        
        return response
    
    def debug_message(self, message):
        dplog.debug(message)
        print message

