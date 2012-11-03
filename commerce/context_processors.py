from app_settings import COMMERCE_THUMBNAIL_SIZE


def thumbnail(request):
    return {
        'COMMERCE_THUMBNAIL_SIZE': COMMERCE_THUMBNAIL_SIZE
    }
