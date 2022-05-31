from commerce import settings


def get_product_availability(product):
    if hasattr(product, 'availability'):
        return product.availability

    key = f'{product._meta.app_label}.{product.__class__.__name__}'
    availability = settings.PRODUCTS_AVAILABILITIES.get(key, None)

    if availability is not None:
        return availability

    raise NotImplementedError('Missing product availability information of %s' % product)
