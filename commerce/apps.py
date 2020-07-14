import django_rq
from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from commerce.cron import send_order_reminders


class Config(AppConfig):
    name = 'commerce'
    verbose_name = _('Commerce')

    def ready(self):
        self.schedule_jobs()

    def schedule_jobs(self):
        print('Scheduling commerce jobs...')
        scheduler = django_rq.get_scheduler('cron')

        # Cron task to send order reminders
        scheduler.cron(
            "0 10 * * *",  # Run every day at 10
            # "* * * * *",  # Run every minute (DEBUG)
            func=send_order_reminders,
            timeout=settings.RQ_QUEUES['cron']['DEFAULT_TIMEOUT']
        )
