from __future__ import division
import os

from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from commerce.app_settings import COMMERCE_TAX
from commerce.models.catalog import Catalog
from commerce.managers.product import ProductManager
from commerce.models.manufacturer import Manufacturer


def product_cover_upload_to(instance, filename):
    file_name, file_extension = os.path.splitext(filename)
    return 'commerce/products/covers/%s%s' % (instance.slug, file_extension)


def product_file_upload_to(instance, filename):
    file_name, file_extension = os.path.splitext(filename)
    return 'commerce/products/files/%s%s' % (instance.slug, file_extension)


class Product(models.Model):
    manufacturer = models.ForeignKey(
        Manufacturer, 'id',
        verbose_name=_(u'manufacturer'), default=None, blank=True, null=True)
    associated_product = models.ForeignKey(
        'self', 'id', verbose_name=_(u'associated product'),
        blank=True, default=None, null=True)
    file = models.FileField(
        _(u'file'),
        upload_to=product_file_upload_to, null=True, blank=True, default=None)
    cover = models.ImageField(
        _(u'image'), upload_to=product_cover_upload_to,
        width_field='cover_width', height_field='cover_height')
    cover_width = models.IntegerField(_(u'width'))
    cover_height = models.IntegerField(_(u'height'))
    catalog = models.ForeignKey(Catalog, 'id', verbose_name=_(u'catalog'))
    title = models.CharField(_(u'title'), max_length=255)
    slug = models.SlugField(
        _(u'slug'), max_length=255, null=True, blank=True, default=None)
    description = models.TextField(_(u'description'))
    price = models.FloatField(_(u'price'))
    price_discount = models.FloatField(
        _(u'price discount'), null=True, blank=True, default=None)
    price_common = models.FloatField(
        _(u'common price'), null=True, blank=True, default=None)
    price_real = models.FloatField(_(u'real price'))
    not_visible_individually = models.BooleanField(
        _(u'not visible individually'), default=False)
    on_stock = models.SmallIntegerField(_(u'on stock'), default=0)
    views = models.PositiveIntegerField(_(u'views'), default=0)
    is_price_with_tax = models.BooleanField(_(u'price with tax'), default=True)
#    is_discount = models.BooleanField(_(u'has discount'), default=False)
    is_new = models.BooleanField(_(u'new'), default=False)
    is_top = models.BooleanField(_(u'top'), default=False)
    created = models.DateTimeField(_(u'created'), default=now())
    modified = models.DateTimeField(_(u'modified'))
    objects = ProductManager()

    class Meta:
        app_label = 'commerce'
        db_table = 'commerce_products'
        verbose_name = _(u'product')
        verbose_name_plural = _(u'products')
        ordering = ('-pk',)

        _(u'moj text %(premenna)s' % {
            'premenna': 'aaa',
        })
    def __unicode__(self):
        if self.associated_product is not None:
            return '%s &rarr; %s' % (self.associated_product.title, self.title)
        return self.title

    def save(self, **kwargs):
        self.modified = now()

        if self.associated_product is not None:
            self.cover = self.associated_product.cover
            self.cover_width = self.associated_product.cover_width
            self.cover_height = self.associated_product.cover_height
            self.catalog = self.associated_product.catalog
            self.manufacturer = self.associated_product.manufacturer
            self.description = self.associated_product.description
            self.not_visible_individually = True

            # Main product price update
            if self.associated_product.product_set.count() is 0:
                self.associated_product.price = self.price
                self.associated_product.price_discount = self.price_discount
                self.associated_product.price_real = self.price_real
                self.associated_product.save()
            elif self.price_discount and self.price_discount < self.associated_product.price_discount:
                self.associated_product.price = self.price
                self.associated_product.price_discount = self.price_discount
                self.associated_product.price_real = self.price_real
                self.associated_product.save()
            elif self.associated_product.price > self.price:
                self.associated_product.price = self.price
                self.associated_product.price_real = self.price_real
                self.associated_product.price_discount = None
                self.associated_product.save()

        super(Product, self).save(**kwargs)

    @models.permalink
    def get_absolute_url(self):
        return 'commerce_products_detail', [self.slug, ]

    def get_associated_products(self):
        return Product.objects.filter(associated_product=self)

    def get_price(self):
        return self.price_real

    def discount_percent(self):
        if self.price_discount:
            return '%.0f%%' % (
                (self.price - self.price_discount) * 100 / self.price,)
        return None
