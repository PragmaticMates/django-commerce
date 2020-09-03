from django.conf import settings


CURRENCY = getattr(settings, 'COMMERCE_CURRENCY', 'EUR')
PAYMENT_MANAGERS = getattr(settings, 'COMMERCE_PAYMENT_MANAGERS', {
    'WIRE_TRANSFER': 'commerce.gateways.wiretransfer.managers.PaymentManager',
    'ONLINE_PAYMENT': 'commerce.gateways.globalpayments.managers.PaymentManager'
})
SUCCESSFUL_PAYMENT_REDIRECT_URL = getattr(settings, 'COMMERCE_SUCCESSFUL_PAYMENT_REDIRECT_URL', '/')
IBAN = getattr(settings, 'COMMERCE_IBAN', '')
BIC_SWIFT = getattr(settings, 'COMMERCE_BIC_SWIFT', '')
BANK_NAME = getattr(settings, 'COMMERCE_BANK_NAME', '')
BANK_ADDRESS = getattr(settings, 'COMMERCE_BANK_ADDRESS', '')
RECIPIENT = getattr(settings, 'COMMERCE_RECIPIENT', '')
RECIPIENT_ADDRESS = getattr(settings, 'COMMERCE_RECIPIENT_ADDRESS', '')
USE_RQ = getattr(settings, 'COMMERCE_USE_RQ', True)
REDIS_QUEUE = getattr(settings, 'COMMERCE_REDIS_QUEUE', 'default')
ORDER_NUMBER_STARTS_FROM = getattr(settings, 'COMMERCE_ORDER_NUMBER_STARTS_FROM', 1)
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
