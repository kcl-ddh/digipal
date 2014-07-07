# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, BadHeaderError
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

@login_required
@csrf_exempt
def send_email(request):
    subject = (request.GET.get('subject', ''))
    message = (request.GET.get('message', ''))
    from_email = (request.GET.get('from_email', ''))
    to_emails = list(request.GET.get('to', ''))

    if subject and message and from_email and to_emails:
        try:
            send_mail(subject, message, from_email, to_emails)
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
    else:
        return HttpResponse('Provide parameters.')
