from django.urls import path
from django.utils.translation import pgettext_lazy
from commerce.views.cart import AddToCartView

app_name = 'commerce'

urlpatterns = [
    path(pgettext_lazy("url", 'add-to-cart/<int:content_type_id>/<int:object_id>/'), AddToCartView.as_view(), name='add_to_cart'),
    # path(pgettext_lazy("url", 'cart/'), CartView.as_view(), name='cart'),
]
