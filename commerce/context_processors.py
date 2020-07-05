from commerce.models import Discount


def valid_promoted_discount_codes(request):
    return {
        'valid_promoted_discount_codes': Discount.objects.valid().promoted().order_by('valid_until'),
        'discount_codes': Discount.objects.all()
    }
