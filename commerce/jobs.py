from django.core.mail import send_mail
from django_rq import job
from commerce import settings as commerce_settings


@job(commerce_settings.REDIS_QUEUE)
def send_mail_in_background(subject, message, from_email, recipient_list, html_message=None, fail_silently=True):
    send_mail(subject, message, from_email, recipient_list, html_message=html_message, fail_silently=fail_silently)


@job(commerce_settings.REDIS_QUEUE)
def send_order_reminders():
    from commerce.models import Order
    unpaid_old_orders = Order.objects.not_reminded().awaiting_payment().old(days=7)
    total_orders = unpaid_old_orders.count()
    print(f'Found {total_orders} old unpaid orders without reminder')

    for order in unpaid_old_orders:
        print(order, order.created.date(), order.total, order.user)
        order.send_reminder()
