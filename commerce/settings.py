from django.conf import settings


CURRENCY = getattr(settings, 'COMMERCE_CURRENCY', 'EUR')
PAYMENT_MANAGERS = getattr(settings, 'COMMERCE_PAYMENT_MANAGERS', {
    'WIRE_TRANSFER': 'commerce.gateways.wiretransfer.managers.PaymentManager',
    'ONLINE_PAYMENT': 'commerce.gateways.globalpayments.managers.PaymentManager'
})
PRODUCTS_AVAILABILITIES = getattr(settings, 'COMMERCE_PRODUCTS_AVAILABILITIES', {})
SUCCESSFUL_PAYMENT_REDIRECT_URL = getattr(settings, 'COMMERCE_SUCCESSFUL_PAYMENT_REDIRECT_URL', '/')
CHECKOUT_FINISH_URL = getattr(settings, 'COMMERCE_CHECKOUT_FINISH_URL', None)
IBAN = getattr(settings, 'COMMERCE_IBAN', '')
BIC_SWIFT = getattr(settings, 'COMMERCE_BIC_SWIFT', '')
BANK_NAME = getattr(settings, 'COMMERCE_BANK_NAME', '')
BANK_ADDRESS = getattr(settings, 'COMMERCE_BANK_ADDRESS', '')
RECIPIENT = getattr(settings, 'COMMERCE_RECIPIENT', '')
RECIPIENT_ADDRESS = getattr(settings, 'COMMERCE_RECIPIENT_ADDRESS', '')
USE_RQ = getattr(settings, 'COMMERCE_USE_RQ', True)
REDIS_QUEUE = getattr(settings, 'COMMERCE_REDIS_QUEUE', 'default')
ORDER_NUMBER_STARTS_FROM = getattr(settings, 'COMMERCE_ORDER_NUMBER_STARTS_FROM', 1)
CREATE_PROFORMA_INVOICE = getattr(settings, 'COMMERCE_CREATE_PROFORMA_INVOICE', False)
LOYALTY_PROGRAM_ENABLED = getattr(settings, 'COMMERCE_LOYALTY_PROGRAM_ENABLED', False)
LOYALTY_POINTS_PER_CURRENCY_UNIT = getattr(settings, 'COMMERCE_LOYALTY_POINTS_PER_CURRENCY_UNIT', 0)
CURRENCY_UNITS_PER_LOYALTY_POINT = getattr(settings, 'COMMERCE_CURRENCY_UNITS_PER_LOYALTY_POINT', 0)
UNIT_PRICE_IS_WITH_TAX = getattr(settings, 'COMMERCE_UNIT_PRICE_IS_WITH_TAX', True)
BANK_API_TOKEN = getattr(settings, 'COMMERCE_BANK_API_TOKEN', None)
BANK_API = getattr(settings, 'COMMERCE_BANK_API', None)
GATEWAY_GP_MERCHANT_NUMBER = getattr(settings, 'COMMERCE_GATEWAY_GP_MERCHANT_NUMBER', None)
GATEWAY_GP_PRIVATE_KEY_PASSWORD = getattr(settings, 'COMMERCE_GATEWAY_GP_PRIVATE_KEY_PASSWORD', None)
GATEWAY_GP_PRIVATE_KEY_PATH = getattr(settings, 'COMMERCE_GATEWAY_GP_PRIVATE_KEY_PATH', None)
GATEWAY_GP_PUBLIC_KEY_PATH = getattr(settings, 'COMMERCE_GATEWAY_GP_PUBLIC_KEY_PATH', None)
GATEWAY_GP_ORDER_NUMBER_STARTS_FROM = getattr(settings, 'COMMERCE_GATEWAY_GP_ORDER_NUMBER_STARTS_FROM', 1)
GATEWAY_GP_DEBUG = getattr(settings, 'COMMERCE_GATEWAY_GP_DEBUG', False)
GATEWAY_GP_URL = 'https://3dsecure.gpwebpay.com/pgw/order.do'
GATEWAY_GP_URL_TEST = 'https://test.3dsecure.gpwebpay.com/pgw/order.do'
GATEWAY_STRIPE_PUBLISHABLE_API_KEY = getattr(settings, 'COMMERCE_GATEWAY_STRIPE_PUBLISHABLE_API_KEY', None)
GATEWAY_STRIPE_SECRET_API_KEY = getattr(settings, 'COMMERCE_GATEWAY_STRIPE_SECRET_API_KEY', None)
GATEWAY_STRIPE_ENDPOINT_SECRET = getattr(settings, 'COMMERCE_GATEWAY_STRIPE_ENDPOINT_SECRET', None)