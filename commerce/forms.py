from crispy_forms.bootstrap import PrependedText, FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Fieldset, Div, Submit
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from commerce.models import Cart


class AddressesForm(forms.ModelForm):
    class Meta:
        model = Cart
        exclude = ['user', 'shipping_option', 'payment_method']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Fieldset(
                    _('Delivery address'),
                    'delivery_name',
                    'delivery_street',
                    'delivery_postcode',
                    'delivery_city',
                    'delivery_country',
                    css_class='col-md-6'
                ),
                Fieldset(
                    _('Billing details'),
                    'billing_name',
                    'billing_street',
                    'billing_postcode',
                    'billing_city',
                    'billing_country',
                    'reg_id',
                    'tax_id',
                    'vat_id',
                    css_class='col-md-6'
                ),
                Fieldset(
                    _('Contact details'),
                    Row(
                        Div(PrependedText('email', '<i class="fas fa-at"></i>'), css_class='col-md-7'),
                        Div(PrependedText('phone', '<i class="far fa-mobile"></i>'), css_class='col-md-5'),
                    ),
                ),
            ),
            FormActions(
                Submit('submit', _('Continue'), css_class='btn-primary')
            )
        )


class ShippingAndPaymentForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ['shipping_option', 'payment_method']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # shipping options
        delivery_country = self.instance.delivery_country
        shipping_options = self.fields['shipping_option'].queryset
        country_shipping_options = shipping_options.filter(countries__contains=[delivery_country])
        shipping_options = country_shipping_options if country_shipping_options.exists() else shipping_options.filter(countries=[])
        self.fields['shipping_option'].queryset = shipping_options

        # form
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Fieldset(
                    _('Select Shipping Option'),
                    'shipping_option',
                    css_class='col-md-6'
                ),
                Fieldset(
                    _('Choose Payment Type'),
                    'payment_method',
                    css_class='col-md-6'
                ),
            ),
            FormActions(
                Submit('submit', _('Continue'), css_class='btn-primary')
            )
        )

    def clean_payment_method(self):
        shipping_option = self.cleaned_data.get('shipping_option', None)
        payment_method = self.cleaned_data.get('payment_method', None)

        if payment_method and shipping_option and shipping_option not in payment_method.shippings.all():
            raise ValidationError(_(f'This payment method is not available for shipping option {shipping_option}'))

        return payment_method
