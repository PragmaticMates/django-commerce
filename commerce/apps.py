import django_rq
from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from commerce.cron import send_order_reminders, cancel_unpaid_orders, delete_old_empty_carts


class Config(AppConfig):
    name = 'commerce'
    verbose_name = _('Commerce')

    def ready(self):
        self.schedule_jobs()

    def schedule_jobs(self):
        print('Scheduling commerce jobs...')
        scheduler = django_rq.get_scheduler('cron')

        # Cron task to cancel unpaid orders
        scheduler.cron(
            "0 9 * * *",  # Run every day at 9:00 [UTC]
            # "* * * * *",  # Run every minute (DEBUG)
            func=cancel_unpaid_orders,
            timeout=settings.RQ_QUEUES['cron']['DEFAULT_TIMEOUT']
        )

        # Cron task to send order reminders
        scheduler.cron(
            "0 10 * * *",  # Run every day at 10:00 [UTC]
            # "* * * * *",  # Run every minute (DEBUG)
            func=send_order_reminders,
            timeout=settings.RQ_QUEUES['cron']['DEFAULT_TIMEOUT']
        )

        # Cron task to delete old empty carts
        scheduler.cron(
            "0 1 * * *",  # Run every day at 01:00 [UTC]
            # "* * * * *",  # Run every minute (DEBUG)
            func=delete_old_empty_carts,
            timeout=settings.RQ_QUEUES['cron']['DEFAULT_TIMEOUT']
        )

        # TODO: delete old abandoned carts (not empty, but youngest item is old already)
        # TODO: notify not empty abandoned carts

        print('Commerce jobs scheduled.')
