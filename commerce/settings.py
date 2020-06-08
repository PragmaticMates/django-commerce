from django.conf import settings


CURRENCY = getattr(settings, 'COMMERCE_CURRENCY', 'EUR')
