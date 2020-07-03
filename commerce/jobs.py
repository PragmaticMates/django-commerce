from django.core.mail import send_mail
from django_rq import job
from commerce import settings as commerce_settings


@job(commerce_settings.REDIS_QUEUE)
def send_mail_in_background(subject, message, from_email, recipient_list, html_message=None, fail_silently=True):
    send_mail(subject, message, from_email, recipient_list, html_message=html_message, fail_silently=fail_silently)
