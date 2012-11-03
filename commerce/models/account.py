from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from commerce.app_settings import COMMERCE_COUNTRIES


class Profile(models.Model):
    user = models.OneToOneField(User, 'id', verbose_name=_(u'user'))
    company_name = models.CharField(
        _(u'company name'),
        max_length=255, default=None, blank=True, null=True)
    company_tax_id = models.CharField(
        _(u'TAX ID'), max_length=255, default=None, blank=True, null=True)
    company_id = models.CharField(
        _(u'ID'), max_length=255, default=None, blank=True, null=True)
    company_vat = models.CharField(
        _(u'VAT'), max_length=255, default=None, blank=True, null=True)

    street_and_number = models.CharField(
        _(u'street and number'), max_length=255)
    city = models.CharField(_(u'city'), max_length=255)
    zip = models.CharField(_(u'ZIP'), max_length=255)
    country = models.CharField(
        _(u'country'), max_length=255, choices=COMMERCE_COUNTRIES)
    phone = models.CharField(
        _(u'phone'), max_length=255, default=None, blank=True, null=True)
    shipping_company_name = models.CharField(
        _(u'company name'),
        max_length=255, default=None, blank=True, null=True)
    shipping_first_name = models.CharField(
        _(u'first name'), max_length=255)
    shipping_last_name = models.CharField(
        _(u'last name'), max_length=255)
    shipping_street_and_number = models.CharField(
        _(u'street and number'), max_length=255)
    shipping_city = models.CharField(_(u'city'), max_length=255)
    shipping_zip = models.CharField(_(u'ZIP'), max_length=255)
    shipping_country = models.CharField(
        _(u'country'), max_length=255, choices=COMMERCE_COUNTRIES)
    is_newsletter = models.BooleanField(_(u'receive newsletter'), default=True)
    created = models.DateTimeField(_(u'created'), default=now())
    modified = models.DateTimeField(_(u'modified'), )

    class Meta:
        app_label = 'commerce'
        db_table = 'commerce_profiles'
        verbose_name = _(u'profile')
        verbose_name_plural = _(u'profiles')

    def __unicode__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    def save(self, **kwargs):
        self.modified = now()
        super(Profile, self).save(**kwargs)
