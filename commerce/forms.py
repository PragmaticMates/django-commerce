from crispy_forms.bootstrap import PrependedText, FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Fieldset, Div, Submit, HTML
from django import forms
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import EMPTY_VALUES
from django.forms import Form, HiddenInput
from django.template import Template, Context, loader
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from commerce import settings as commerce_settings
from commerce.models import Cart, Discount, ShippingOption
from commerce.loyalty import available_points


class DiscountCodeForm(forms.ModelForm):
    discount = forms.CharField(label=_('Discount code'), required=False)
    loyalty_points = forms.IntegerField(label=_('Loyalty points'), required=False)

    class Meta:
        model = Cart
        fields = ['discount', 'loyalty_points']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'discount-and-loyalty-points'

        # Discount
        discount_form_input = 'discount'
        if self.instance.discount:
            discount = self.instance.discount
            types = discount.content_types.all()
            discount_form_input = HTML('<label>%(label)s</label><br><i>%(code)s</i> = %(amount)s %(content_types)s<br>%(link)s' % {
                'label': _('Discount code'),
                'code': discount.code,
                'amount': discount.get_amount_display(),
                'content_types': '(%s)' % ', '.join([str(t) for t in types]) if types.all().exists() else '',
                'link': f"<a href=\"{reverse('commerce:unapply_discount')}\">{_('Remove')}</a>"
            })

        # Loyalty program
        if commerce_settings.LOYALTY_PROGRAM_ENABLED:
            self.available_points_to_use = available_points(self.instance)
            self.fields['loyalty_points'].help_text = _('You can use %d points') % self.available_points_to_use
            loyalty_points_form_input = Div('loyalty_points', css_class='col-md')
        else:
            self.fields['loyalty_points'].widget = HiddenInput()
            loyalty_points_form_input = ''

        self.helper.layout = Layout(
            Row(
                Div(discount_form_input, css_class='col-md'),
                loyalty_points_form_input,
                FormActions(
                    Submit('submit', _('Apply'), css_class='btn-secondary'),
                    css_class='col-md mt-4 pt-2'
                ) if commerce_settings.LOYALTY_PROGRAM_ENABLED or not self.instance.discount else ''
            ),
        )

    def clean_discount(self):
        discount = None
        code = self.cleaned_data.get('discount', None)

        if code not in EMPTY_VALUES:
            try:
                discount = Discount.objects.get(code=code)

                if not discount.is_valid:
                    raise ValidationError(_('Discount code %s is not valid anymore') % discount.code)

                if discount.is_used:
                    raise ValidationError(_('Discount code %s was used already') % discount.code)

            except ObjectDoesNotExist:
                raise ValidationError(_('There is no such discount code'))

        return discount

    def clean_loyalty_points(self):
        loyalty_points = self.cleaned_data.get('loyalty_points', 0) or 0
        return min(loyalty_points, self.available_points_to_use) if commerce_settings.LOYALTY_PROGRAM_ENABLED else 0


class AddressesForm(forms.ModelForm):
    class Meta:
        model = Cart
        exclude = ['user', 'shipping_option', 'payment_method', 'discount']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'checkout-form checkout-form-addresses'
        self.helper.layout = Layout(
            Div(
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
                ),
                css_class='row'
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
        self.fields['shipping_option'].queryset = ShippingOption.objects.for_country(self.instance.delivery_country)

        # form
        self.helper = FormHelper()
        self.helper.form_class = 'checkout-form checkout-shipping-and-payment'
        self.helper.layout = Layout(
            Div(
                Fieldset(
                    _('Select Shipping Option'),
                    'shipping_option',
                    HTML(loader.get_template('commerce/fees.html').render({'fees': self.fields['shipping_option'].queryset})),
                    css_class='col-md-6'
                ),
                Fieldset(
                    _('Choose Payment Type'),
                    'payment_method',
                    HTML(loader.get_template('commerce/fees.html').render({'fees': self.fields['payment_method'].queryset})),
                    css_class='col-md-6'
                ),
                css_class='row'
            ),
            FormActions(
                Submit('submit', _('Continue'), css_class='btn-primary mt-3')
            )
        )

    def clean_payment_method(self):
        shipping_option = self.cleaned_data.get('shipping_option', None)
        payment_method = self.cleaned_data.get('payment_method', None)

        if payment_method and shipping_option and shipping_option not in payment_method.shippings.all():
            raise ValidationError(_('This payment method is not available for shipping option %s') % shipping_option)

        return payment_method


class PurchasedItemFileForm(Form):
    purchased_item_id = forms.IntegerField()
    file = forms.FileField()
