from django import http
from django.conf import settings
import re
from digipal.utils import dplog
from django.http.response import Http404

# TODO: log the perfs to a file instead of printing them out


def are_perf_info_enabled():
    return getattr(settings, 'DEBUG', False) and getattr(settings, 'DEBUG_PERFORMANCE', False)


class ErrorMiddleware(object):
    def process_exception(self, request, exception):
        '''
            Django doesn't pass the Http404 message to the template
            by default. So we have to do it ourself here.
        '''
        if isinstance(exception, Http404):
            from django.shortcuts import render
            args = list(exception.args[:])
            context = {}
            context['reason'] = args.pop(0) if args else ''
            context['title'] = args.pop(0) if args else ''
            return render(request, 'errors/404.html', context, status=404)
        else:
            return None


class HttpsAdminMiddleware(object):
    def process_request(self, request):
        from datetime import datetime
        request.start_time = datetime.now()

        if are_perf_info_enabled():
            dplog('START REQUEST' + '-' * 60)

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
            dplog('%s (%s)' %
                  (request.path, request.stop_time - request.start_time))
            dplog('END RESPONSE' + '-' * 60)

        return response
