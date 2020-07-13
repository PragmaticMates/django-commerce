from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template import loader, TemplateDoesNotExist
from commerce import settings as commerce_settings
from commerce.jobs import send_mail_in_background


class PaymentManager(object):
    def __init__(self, order):
        self.order = order

    def render_payment_button(self):
        raise NotImplementedError()

    def render_payment_information(self):
        raise NotImplementedError()


class EmailManager(object):
    @staticmethod
    def send_mail(recipient, event, subject, data=None, request=None):
        # template
        try:
            t = loader.get_template('commerce/mails/{}.txt'.format(event.lower()))
        except TemplateDoesNotExist:
            t = None

        # HTML template
        try:
            t_html = loader.get_template('commerce/mails/{}.html'.format(event.lower()))
        except TemplateDoesNotExist:
            t_html = None

        # recipients
        recipient_list = [recipient.email]

        site = get_current_site(request)

        # context
        context = {
            'recipient': recipient,
            'event': event,
            'subject': subject,
            'request': request,
            'site': site
        }

        if data:
            context.update(data)

        # message
        message = t.render(context) if t else ''
        html_message = t_html.render(context) if t_html else ''

        if commerce_settings.USE_RQ:
            send_mail_in_background.delay(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message, fail_silently=False)
        else:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message, fail_silently=False)
