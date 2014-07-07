# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, BadHeaderError

@login_required
def send_email(request):
    subject = request.POST.get('subject', '')
    message = request.POST.get('message', '')
    from_email = request.POST.get('from_email', '')
    to_emails = request.POST.get('to', '')

    if subject and message and from_email and to_emails:
        for address in to_emails:
            try:
                send_mail(subject, message, from_email, address)
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
