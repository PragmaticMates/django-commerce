from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template import loader, Context
from django.utils.translation import ugettext_lazy as _

from commerce.models.order import Order
from commerce.app_settings import COMMERCE_EMAIL_FROM, \
    COMMERCE_STATE_PROCESS, COMMERCE_STATE_SHIPPED, COMMERCE_URL, \
    COMMERCE_THUMBNAIL_SIZE


@receiver(pre_save, sender=Order)
def order_shipped(sender, **kwargs):
    new = kwargs.get('instance')
    if new.pk is not None:
        old = Order.objects.get(pk=new.pk)

        if old.state == COMMERCE_STATE_PROCESS:
            if new.state == COMMERCE_STATE_SHIPPED:
                t = loader.get_template('commerce/mails/order-shipped.html')
                c = Context({
                    'order': kwargs.get('instance'),
                    'host': COMMERCE_URL,
                    'size': COMMERCE_THUMBNAIL_SIZE,
                })

                message = EmailMultiAlternatives(
                    _(u'Order shipped'), '',
                    COMMERCE_EMAIL_FROM, [kwargs.get('instance').user.email])
                message.attach_alternative(t.render(c), 'text/html')
                message.send()
