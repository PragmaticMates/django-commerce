from django.contrib.auth import get_user_model
from django_rq import job
from commerce import settings as commerce_settings
from commerce.loyalty import unused_points, send_loyalty_reminder


@job(commerce_settings.REDIS_QUEUE)
def send_order_reminders():
    from commerce.models import Order
    unpaid_old_orders = Order.objects.not_reminded().awaiting_payment().old(days=7)
    total_orders = unpaid_old_orders.count()
    print(f'Found {total_orders} old unpaid orders without reminder')

    for order in unpaid_old_orders:
        print(order, order.created.date(), order.total, order.user)
        order.send_reminder()


@job(commerce_settings.REDIS_QUEUE)
def cancel_unpaid_orders():
    from commerce.models import Order
    from invoicing.models import Invoice

    unpaid_old_orders = Order.objects.awaiting_payment().old(days=14)
    total_orders = unpaid_old_orders.count()
    print(f'Found {total_orders} old unpaid orders')

    for order in unpaid_old_orders:
        print(order, order.created.date(), order.total, order.user)
        order.status = Order.STATUS_CANCELLED
        order.save(update_fields=['status'])

        # cancel invoices
        for invoice in order.invoices.filter(
                type=Invoice.TYPE.INVOICE,
                status__in=[
                    Invoice.STATUS.NEW,
                    Invoice.STATUS.SENT,
                    Invoice.STATUS.RETURNED]):
            invoice.status = Invoice.STATUS.CANCELED
            invoice.save(update_fields=['status'])


@job(commerce_settings.REDIS_QUEUE)
def delete_old_empty_carts():
    from commerce.models import Cart

    empty_old_carts = Cart.objects.old().empty()
    total_carts = empty_old_carts.count()
    print(f'Found {total_carts} old empty carts')
    empty_old_carts.delete()


@job(commerce_settings.REDIS_QUEUE)
def send_loyalty_reminders():
    from commerce.models import Order
    days = 7
    orders = Order.objects.with_earned_loyalty_points().old(days=days, interval='exact')
    total_orders = orders.count()

    print(f'Found {total_orders} orders with loyalty points {days} old exactly days')
    users = get_user_model().objects.filter(id__in=orders.values('user')).distinct()

    for user in users:
        send_loyalty_reminder(user)
