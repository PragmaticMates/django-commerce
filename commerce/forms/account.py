from form_utils.forms import BetterModelForm

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from commerce.app_settings import COMMERCE_COUNTRIES
from commerce.models.account import Profile

PASSWORD_MIN_SIZE = 6


class RecoverForm(forms.Form):
    email = forms.EmailField(label=_(u'Email'), required=True)


class ProfileForm(BetterModelForm):
    first_name = forms.CharField(label=_(u'First name'), required=True)
    last_name = forms.CharField(label=_(u'Last name'), required=True)
    country = forms.CharField(
        label=_(u'Country'),
        required=True, widget=forms.Select(choices=COMMERCE_COUNTRIES))
    shipping_country = forms.CharField(
        label=_(u'Country'),
        required=True, widget=forms.Select(choices=COMMERCE_COUNTRIES))

    class Meta:
        model = Profile
        fieldsets = [
            (_(u'Invoicing information'), {
                'fields': (
                    'first_name', 'last_name', 'street_and_number', 'city',
                    'zip', 'country', 'company_name', 'company_tax_id',
                    'company_id', 'company_vat', 'phone'),
                'classes': ('invoicing', ),
            }),
            (_(u'Shipping information'), {
                'fields': ('shipping_first_name', 'shipping_last_name',
                           'shipping_street_and_number', 'shipping_city',
                           'shipping_zip', 'shipping_country',
                           'shipping_company_name',),
                'classes': ('shipping', ),
            }),
            (None, {
                'fields': ('is_newsletter',),
                'classes': ('misc', ),
            })
        ]


class CheckoutProfileForm(ProfileForm):
    class Meta:
        model = Profile
        fieldsets = [
            (_(u'Invoicing information'), {
                'fields': (
                    'first_name', 'last_name',
                    'street_and_number', 'city', 'zip', 'country',
                    'company_name', 'company_tax_id', 'company_id',
                    'company_vat', 'phone'),
                'classes': ('invoicing', ),
            }),
            (_(u'Shipping information'), {
                'fields': ('shipping_first_name', 'shipping_last_name',
                           'shipping_street_and_number', 'shipping_city',
                           'shipping_zip', 'shipping_country',
                           'shipping_company_name',),
                'classes': ('shipping', ),
            }),
        ]


class RegistrationForm(forms.Form):
    username = forms.CharField(label=_(u'Email'), required=True)
    password = forms.CharField(
        label=_(u'Password'), required=True,
        widget=forms.PasswordInput(), min_length=PASSWORD_MIN_SIZE)
    retype = forms.CharField(
        label=_(u'Confirm password'), required=True,
        widget=forms.PasswordInput(), min_length=PASSWORD_MIN_SIZE)

    def clean_username(self):
        username = self.cleaned_data.get('username', None)
        try:
            User.objects.get(username=username)
            raise forms.ValidationError(_('Username already exists.'))
        except ObjectDoesNotExist:
            return username

    def clean_retype(self):
        password = self.cleaned_data.get('password')
        retype = self.cleaned_data.get('retype')
        if retype != password:
            raise forms.ValidationError(
                _(u'Password and confirmed password did not match.'))
        return retype


class LoginForm(forms.Form):
    username = forms.EmailField(label=_(u'Email'), required=True)
    password = forms.CharField(
        label=_(u'Password'), required=True,
        widget=forms.PasswordInput(), min_length=PASSWORD_MIN_SIZE)


class PasswordForm(forms.Form):
    old_password = forms.CharField(
        label=_(u'Old password'), required=True,
        min_length=PASSWORD_MIN_SIZE, widget=forms.PasswordInput())
    new_password = forms.CharField(
        label=_(u'New password'), required=True,
        min_length=PASSWORD_MIN_SIZE, widget=forms.PasswordInput())
    retype = forms.CharField(
        label=_(u'Retype password'), required=True,
        min_length=PASSWORD_MIN_SIZE, widget=forms.PasswordInput())

    def __init__(self, user, *args, **kwargs):
        super(PasswordForm, self).__init__(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        data = self.cleaned_data
        if self.user.check_password(data.get('old_password', None)) is False:
            raise forms.ValidationError(_(u'Old password is not correct'))
        return data.get('old_password')

    def clean_retype(self):
        data = self.cleaned_data

        if data.get('new_password', None) != data.get('retype', None):
            raise forms.ValidationError(
                _(u'New and retyped password must be same.'))

        return data.get('retype', None)
