# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, BadHeaderError
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

@login_required
@csrf_exempt
def send_email(request):
    subject = request.GET.get('subject', '')
    message = request.GET.get('message', '')
    from_email = request.GET.get('from_email', '')
    to_emails = request.GET.getlist('to')
    if subject and message and from_email and to_emails:
        try:
            if send_mail(subject, message, from_email, to_emails):
                return HttpResponse("Email succesfully sent")
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
    else:
        return HttpResponse('Provide parameters.')
