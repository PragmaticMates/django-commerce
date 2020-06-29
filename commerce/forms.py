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
        self.helper.form_class = 'checkout-form checkout-form-addresses'
        self.helper.layout = Layout(
            Row(
                Fieldset(
                    _('Delivery address'),
                    'delivery_name',
                    'delivery_street',
                    Row(
                        Div('delivery_postcode', css_class='col-md-6'),
                        Div('delivery_city', css_class='col-md-6')
                    ),
                    'delivery_country',
                    Row(
                        Div(PrependedText('email', '<i class="fas fa-at"></i>'), css_class='col-md-7'),
                        Div(PrependedText('phone', '<i class="far fa-mobile"></i>'), css_class='col-md-5'),
                    ),
                    css_class='col-md-6'
                ),
                Fieldset(
                    _('Billing details'),
                    'billing_name',
                    'billing_street',
                    Row(
                        Div('billing_postcode', css_class='col-md-6'),
                        Div('billing_city', css_class='col-md-6')
                    ),
                    'billing_country',
                    Row(
                        Div('reg_id', css_class='col-md-4'),
                        Div('tax_id', css_class='col-md-4'),
                        Div('vat_id', css_class='col-md-4')
                    ),
                    css_class='col-md-6'
                )
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

        self.fields['shipping_option'].label = ''
        self.fields['payment_method'].label = ''

        # shipping options
        delivery_country = self.instance.delivery_country
        shipping_options = self.fields['shipping_option'].queryset
        country_shipping_options = shipping_options.filter(countries__contains=[delivery_country])
        shipping_options = country_shipping_options if country_shipping_options.exists() else shipping_options.filter(countries=[])
        self.fields['shipping_option'].queryset = shipping_options

        # form
        self.helper = FormHelper()
        self.helper.form_class = 'checkout-form checkout-shipping-and-payment'
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
            raise ValidationError(_('This payment method is not available for shipping option %s') % shipping_option)

        return payment_method