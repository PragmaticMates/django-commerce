from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, EMPTY_VALUES, MaxValueValidator
from django.db import models, transaction
from django.db.models import Sum, CheckConstraint, Q
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _, ugettext, override as override_language
from filer.models import File
from gm2m import GM2MField
from internationalflavor.countries import CountryField
from internationalflavor.vat_number import VATNumberField
from modeltrans.fields import TranslationField

from commerce import settings as commerce_settings
from commerce.helpers import get_product_availability
from commerce.loyalty import points_to_currency_unit, currency_units_to_points, available_points
from commerce.querysets import OrderQuerySet, PurchasedItemQuerySet, DiscountCodeQuerySet, ShippingOptionQuerySet, CartQuerySet
from invoicing.models import Invoice, Item as InvoiceItem
from pragmatic.fields import ChoiceArrayField
from pragmatic.managers import EmailManager
from pragmatic.mixins import SlugMixin


class AbstractProduct(models.Model):
    AVAILABILITY_STOCK = 'STOCK'
    AVAILABILITY_INFINITE = 'INFINITE'
    AVAILABILITY_DIGITAL_GOODS = 'DIGITAL_GOODS'
    AVAILABILITY_SALE_ENDED = 'SALE_ENDED'
    AVAILABILITIES = [
        (AVAILABILITY_STOCK, _('stock')),
        (AVAILABILITY_INFINITE, _('infinite')),
        (AVAILABILITY_DIGITAL_GOODS, _('digital goods')),
        (AVAILABILITY_SALE_ENDED, _('sale ended')),
    ]
    availability = models.CharField(_('availability'), choices=AVAILABILITIES, max_length=13, default=AVAILABILITY_STOCK)

    # TODO: is_stock is deprecated: use property to retrieve stock by supplies and orders
    # in_stock = models.SmallIntegerField(_('in stock'), help_text=_('empty value means infinite availability'), validators=[MinValueValidator(0)], blank=True, null=True, default=None)
    price = models.DecimalField(_('price'), help_text=commerce_settings.CURRENCY, max_digits=10, decimal_places=2, db_index=True, validators=[MinValueValidator(0)],
                                blank=True, null=True, default=None)
    # discount = models.DecimalField(_(u'discount (%)'), max_digits=4, decimal_places=1, default=0)
    awaiting = models.BooleanField(_('awaiting'), default=False)  # TODO: move to availability?
    options = models.ManyToManyField('commerce.Option', verbose_name=_('options'), blank=True)

    # WARNING! don't use generic relation in parent classes. Add them into child classes instead
    # cart_items = GenericRelation('commerce.Item', related_query_name='product')
    # purchased_items = GenericRelation('commerce.PurchasedItem', content_type_field='content_type', object_id_field='object_pk',
    #                            related_query_name='product')

    class Meta:
        abstract = True

    def get_add_to_cart_url(self):
        content_type = ContentType.objects.get_for_model(self)
        return reverse('commerce:add_to_cart', args=(content_type.id, self.id))

    @cached_property
    def total_supplies(self):
        total_supplies = self.supplies.all().aggregate(sum=Sum('quantity'))['sum']
        return total_supplies or 0

    @cached_property
    def purchased(self):
        # count order items of not cancelled orders
        purchased_items = PurchasedItem.objects.filter(
            # product=self
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.id
        ).of_not_cancelled_nor_refunded_orders()
        quantity = purchased_items.aggregate(sum=Sum('quantity'))['sum']
        return quantity or 0

    @cached_property
    def in_stock(self):
        if self.availability == self.AVAILABILITY_INFINITE:
            return 99999  # TODO: more sophisticated solution

        return self.total_supplies - self.purchased


class ShippingOption(models.Model):
    title = models.CharField(_('title'), max_length=50)
    fee = models.DecimalField(_('fee'), help_text=commerce_settings.CURRENCY, max_digits=10, decimal_places=2, db_index=True, validators=[MinValueValidator(0)])
    countries = ChoiceArrayField(verbose_name=_('countries'),
                                 base_field=CountryField(verbose_name=_('country')), size=100,
                                 blank=True, default=list)
    i18n = TranslationField(fields=('title',))
    objects = ShippingOptionQuerySet.as_manager()

    class Meta:
        verbose_name = _('shipping option')
        verbose_name_plural = _('shipping options')
        ordering = ('fee',)
        indexes = [GinIndex(fields=["i18n"]), ]

    def __str__(self):
        return self.title_i18n

    def get_fee_display(self):
        return f'{self.fee} {commerce_settings.CURRENCY}'


class PaymentMethod(models.Model):
    METHOD_CASH_ON_DELIVERY = 'CASH_ON_DELIVERY'
    METHOD_WIRE_TRANSFER = 'WIRE_TRANSFER'
    METHOD_ONLINE_PAYMENT = 'ONLINE_PAYMENT'
    METHOD_PAYPAL = 'PAYPAL'
    METHODS = [
        (METHOD_CASH_ON_DELIVERY, _('cash on delivery')),
        (METHOD_WIRE_TRANSFER, _('wire transfer')),
        (METHOD_ONLINE_PAYMENT, _('online payment')),
        (METHOD_PAYPAL, 'PayPal'),
    ]

    title = models.CharField(_('title'), max_length=50)
    method = models.CharField(_('method'), choices=METHODS, max_length=16)
    fee = models.DecimalField(_('fee'), help_text=commerce_settings.CURRENCY, max_digits=10, decimal_places=2, db_index=True, validators=[MinValueValidator(0)])
    shippings = models.ManyToManyField(ShippingOption)
    i18n = TranslationField(fields=('title',))

    class Meta:
        verbose_name = _('payment method')
        verbose_name_plural = _('payment methods')
        ordering = ('fee',)
        indexes = [GinIndex(fields=["i18n"]), ]

    def __str__(self):
        return self.title_i18n

    def get_fee_display(self):
        return f'{self.fee} {commerce_settings.CURRENCY}'


class Discount(models.Model):
    USAGE_ONE_TIME = 'ONE_TIME'
    USAGE_INFINITE = 'INFINITE'
    USAGES = [
        (USAGE_ONE_TIME, _('one-time only')),
        (USAGE_INFINITE, _('infinite')),
    ]
    UNIT_PERCENTAGE = 'PERCENTAGE'
    UNIT_CURRENCY = 'CURRENCY'
    UNITS = [
        (UNIT_PERCENTAGE, _('percentage')),
        (UNIT_CURRENCY, _('currency')),
    ]
    code = models.CharField(_('code'), max_length=10, unique=True)
    amount = models.PositiveSmallIntegerField(verbose_name=_('amount'))
    unit = models.CharField(_('unit'), max_length=10, choices=UNITS, default=UNIT_PERCENTAGE)
    usage = models.CharField(_('usage'), choices=USAGES, max_length=8)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'), on_delete=models.SET_NULL,
                             blank=True, null=True, default=None)
    description = models.CharField(_('description'), max_length=100)
    valid_until = models.DateTimeField(_('valid until'), db_index=True, blank=True, null=True, default=None)
    promoted = models.BooleanField(_('promoted'), default=False, help_text=_('show in topbar'))
    add_to_cart = models.BooleanField(_('add to cart'), default=False, help_text=_('automatically'))
    content_types = models.ManyToManyField(ContentType, verbose_name=_('content types'), blank=True)
    max_items = models.PositiveSmallIntegerField(_('max items in cart'), blank=True, null=True, default=None)
    products = GM2MField(verbose_name=_('products'), blank=True, related_name='discounts')
    i18n = TranslationField(fields=('description',))
    objects = DiscountCodeQuerySet.as_manager()

    class Meta:
        verbose_name = _('discount')
        verbose_name_plural = _('discounts')
        ordering = ('valid_until',)
        indexes = [GinIndex(fields=["i18n"]), ]
        constraints = [
            CheckConstraint(
                check=Q(amount__gte=0, amount__lte=100, unit='PERCENTAGE') |
                      Q(unit='CURRENCY'),
                name='percentage'
            )
        ]

    def __str__(self):
        return str(self.code)

    def clean(self):
        if self.unit == self.UNIT_PERCENTAGE and (self.amount < 0 or self.amount > 100):
            raise ValidationError(_('Amount of percentage has to be from interval 0-100.'))

        # TODO: content types (m2m) are added after instance save().
        if self.unit == self.UNIT_CURRENCY and self.id and self.content_types.exists():
            raise ValidationError(_("Content types can't be used together with currency type"))

        return super().clean()

    def get_unit_display(self):
        return '%' if self.unit == self.UNIT_PERCENTAGE else commerce_settings.CURRENCY

    def get_amount_display(self):
        return f'-{self.amount} {self.get_unit_display()}'

    @property
    def is_valid(self):
        return self.valid_until is None or self.valid_until > now()

    @property
    def is_used(self):
        if self.usage == self.USAGE_INFINITE:
            return False

        in_cart = Cart.objects.filter(discount=self).exists()

        if in_cart:
            return True

        in_order = Order.objects.filter(discount=self).exists()

        return in_order

    @property
    def is_used_in_order(self):
        return Order.objects.filter(discount=self).exists()

    def can_be_used_in_cart(self, cart):
        if not self.is_valid:
            return False

        if self.max_items is not None and cart.item_set.count() > self.max_items:
            return False

        if self.products.exists():
            if not cart.has_item(list(self.products.all())):
                return False

        return True


class Cart(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)

    # delivery information
    delivery_name = models.CharField(_('full name or company name'), max_length=100, db_index=True)
    delivery_street = models.CharField(_('street and number'), max_length=200)
    delivery_postcode = models.CharField(_('postcode'), max_length=30)
    delivery_city = models.CharField(_('city'), max_length=50)
    delivery_country = CountryField(verbose_name=_('country'), db_index=True)

    # billing address
    billing_name = models.CharField(_('full name or company name'), max_length=100)
    billing_street = models.CharField(_('street and number'), max_length=200)
    billing_postcode = models.CharField(_('postcode'), max_length=30)
    billing_city = models.CharField(_('city'), max_length=50)
    billing_country = CountryField(verbose_name=_('country'), db_index=True)

    # billing company details
    reg_id = models.CharField(_('Company Registration No.'), max_length=30, blank=True)
    tax_id = models.CharField(verbose_name=_('TAX ID'), max_length=30, blank=True)
    vat_id = VATNumberField(verbose_name=_('VAT ID'), blank=True)

    # Contact details
    email = models.EmailField(_('email'))
    phone = models.CharField(_('phone'), max_length=30, blank=True)

    # Shipping and Payment
    shipping_option = models.ForeignKey(ShippingOption, verbose_name=_('shipping option'), on_delete=models.PROTECT, null=True, default=None)
    payment_method = models.ForeignKey(PaymentMethod, verbose_name=_('payment method'), on_delete=models.PROTECT, null=True, default=None)

    # Discount
    discount = models.ForeignKey(Discount, verbose_name=_('discount'), on_delete=models.PROTECT, blank=True, null=True, default=None)

    # Loyalty program
    loyalty_points = models.PositiveSmallIntegerField(_('loyalty points'), help_text=_('used to lower the total price'), blank=True, default=0)

    # Datetimes
    created = models.DateTimeField(_('created'), auto_now_add=True, db_index=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    objects = CartQuerySet.as_manager()

    class Meta:
        verbose_name = _('shopping cart')
        verbose_name_plural = _('shopping carts')

    def __str__(self):
        return ugettext(f'Shopping cart of {self.user}')

    @transaction.atomic
    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)

        if self.subtotal < 0 < self.loyalty_points:
            self.update_loyalty_points()

        return result

    def update_loyalty_points(self):
        self.loyalty_points = available_points(self)
        super().save(update_fields=['loyalty_points'])

    def get_absolute_url(self):
        return reverse('commerce:cart')

    @classmethod
    def get_for_user(cls, user):
        return cls.objects.get_or_create(user=user)[0]

    @property
    def shipping_options(self):
        return ShippingOption.objects.for_country(self.delivery_country)

    @property
    def has_only_free_shipping_options(self):
        return not self.shipping_options.not_free().exists()

    @property
    def delivery_details_required(self):
        return not self.has_only_digital_goods()

    @property
    def billing_details_required(self):
        return self.total != 0 or not self.has_only_free_shipping_options

    @property
    def shipping_fee(self):
        return self.shipping_option.fee if self.shipping_option else 0

    def get_subtotal_display(self):
        return f'{self.subtotal} {commerce_settings.CURRENCY}'

    def get_items_subtotal_display(self):
        return f'{self.items_subtotal} {commerce_settings.CURRENCY}'

    def get_loyalty_points_display(self):
        return f'{self.loyalty_points} (-{points_to_currency_unit(self.loyalty_points)} {commerce_settings.CURRENCY})'

    def get_shipping_fee_display(self):
        return f'{self.shipping_fee} {commerce_settings.CURRENCY}'

    @property
    def payment_fee(self):
        return self.payment_method.fee if self.payment_method else 0

    def get_payment_fee_display(self):
        return f'{self.payment_fee} {commerce_settings.CURRENCY}'

    @property
    def items_subtotal(self):
        return sum([item.subtotal for item in self.item_set.all()])

    @property
    def subtotal(self):
        subtotal = self.items_subtotal

        # discount
        if self.discount and self.discount.unit == Discount.UNIT_CURRENCY:
            subtotal -= self.discount.amount

        # loyalty program
        subtotal -= points_to_currency_unit(self.loyalty_points_used)

        return max(subtotal, 0)
    
    @property
    def loyalty_points_earned(self):
        return currency_units_to_points(self.total)

    @property
    def loyalty_points_used(self):
        return self.loyalty_points

    @property
    def total(self):
        total = self.subtotal
        total += self.shipping_fee
        total += self.payment_fee

        # Note: discount is already calculated in subtotal (item price)

        return total

    def get_total_display(self):
        return f'{self.total} {commerce_settings.CURRENCY}'

    @property
    def open(self):
        return now() - self.created

    @property
    def items_quantity(self):
        return sum([item.quantity for item in self.item_set.all()])

    def is_empty(self):
        return self.items_quantity <= 0

    def can_be_finished(self):
        # TODO: check if all fields are set

        if not self.shipping_option:
            return False

        if self.total < 0:
            return False

        if self.total > 0 and not self.payment_method:
            return False

        return not self.is_empty()

    def has_item(self, product_or_list, option=None):
        if isinstance(product_or_list, list):
            for product in product_or_list:
                if self.has_item(product, option):
                    return True
            return False

        product = product_or_list

        kwargs = {
            'content_type': ContentType.objects.get_for_model(product),
            'object_id': product.id
        }

        if option:
            kwargs.update({
                'option': option
            })

        return self.item_set.filter(**kwargs).exists()

    def has_item_of_type(self, model):
        return self.item_set.filter(
            content_type=ContentType.objects.get_for_model(model),
        ).exists()

    def has_only_digital_goods(self):
        not_digital_goods = filter(
            lambda i: get_product_availability(i.product) != AbstractProduct.AVAILABILITY_DIGITAL_GOODS,
            self.item_set.all()
        )
        return len(list(not_digital_goods)) == 0

    def add_item(self, product, option=None):
        item, created = Item.objects.get_or_create(
            cart=self,
            content_type=ContentType.objects.get_for_model(product),
            object_id=product.id,
            option=option
        )

        if not created:
            item.quantity += 1
            item.save(update_fields=['quantity'])

        # call custom signal
        cart_updated.send(sender=self.__class__, item=item)

        return item

    def to_order(self, status):
        if not self.can_be_finished():
            return None

        # create order with cart data
        order = Order.objects.create(
            user=self.user,
            status=status,
            delivery_name=self.delivery_name,
            delivery_street=self.delivery_street,
            delivery_postcode=self.delivery_postcode,
            delivery_city=self.delivery_city,
            delivery_country=self.delivery_country,
            billing_name=self.billing_name,
            billing_street=self.billing_street,
            billing_postcode=self.billing_postcode,
            billing_city=self.billing_city,
            billing_country=self.billing_country,
            reg_id=self.reg_id,
            tax_id=self.tax_id,
            vat_id=self.vat_id,
            email=self.email,
            phone=self.phone,
            shipping_option=self.shipping_option,
            shipping_fee=self.shipping_fee,
            payment_method=self.payment_method,
            payment_fee=self.payment_fee,
            discount=self.discount,
            loyalty_points=self.loyalty_points
        )

        for item in self.item_set.all():
            PurchasedItem.objects.create(
                order=order,
                content_type=item.content_type,
                object_id=item.object_id,
                quantity=item.quantity,
                price=item.price,
                option=item.option
            )

        if order:
            # delete not useful cart anymore
            self.delete()

        # call custom signal
        checkout_finished.send(sender=self.__class__, order=order)

        # return order
        return order


class Option(SlugMixin, models.Model):
    title = models.CharField(_('title'), max_length=100, unique=True)
    slug = models.SlugField(unique=True, max_length=150, blank=True, db_index=True)
    content_type = models.ForeignKey(
        ContentType, verbose_name=_('content type'), on_delete=models.SET_NULL,
        blank=True, null=True, default=None)  # or many to many?
    i18n = TranslationField(fields=('title', 'slug'))

    class Meta:
        verbose_name = _('option')
        verbose_name_plural = _('options')
        ordering = ('title',)
        indexes = [GinIndex(fields=["i18n"]), ]

    def __str__(self):
        return self.title_i18n

    def total_supplies(self, product):
        total_supplies = product.supplies.filter(
            # product=product,  # AbstractModel
            content_type=ContentType.objects.get_for_model(product),
            object_id=product.id,
            option=self).aggregate(sum=Sum('quantity'))['sum']
        return total_supplies or 0

    def purchased(self, product):
        # count order items of not cancelled orders
        purchased_items = PurchasedItem.objects.filter(
            # product=self  # AbstractModel
            content_type=ContentType.objects.get_for_model(product),
            object_id=product.id,
            option=self
        ).of_not_cancelled_nor_refunded_orders()
        quantity = purchased_items.aggregate(sum=Sum('quantity'))['sum']
        return quantity or 0

    def in_stock(self, product):
        if product.availability == AbstractProduct.AVAILABILITY_INFINITE:
            return 99999  # TODO: more sophisticated solution

        return self.total_supplies(product) - self.purchased(product)


class Item(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey('content_type', 'object_id')
    option = models.ForeignKey(Option, on_delete=models.PROTECT, blank=True, null=True, default=None)
    quantity = models.PositiveSmallIntegerField(verbose_name=_('quantity'), default=1)
    created = models.DateTimeField(_('created'), auto_now_add=True, db_index=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    class Meta:
        verbose_name = _('item')
        verbose_name_plural = _('items')

    def __str__(self):
        return str(self.product)

    def get_absolute_url(self):
        return self.product.get_absolute_url()

    @property
    def regular_price(self):
        return self.product.price

    def get_regular_price_display(self):
        return f'{self.regular_price} {commerce_settings.CURRENCY}'

    @property
    def price(self):
        product = self.product
        discount = self.cart.discount

        if discount and discount.unit == Discount.UNIT_PERCENTAGE:
            if Discount.objects.for_product(product).filter(id=discount.id).exists():
                from commerce.templatetags.commerce import percentage_discount_price
                return Decimal(percentage_discount_price(product.price, discount.amount))

        return self.regular_price

    def get_price_display(self):
        return f'{self.price} {commerce_settings.CURRENCY}'

    @property
    def subtotal(self):
        return self.quantity * self.price

    def get_subtotal_display(self):
        return f'{self.subtotal} {commerce_settings.CURRENCY}'


class Order(models.Model):
    STATUS_AWAITING_PAYMENT = 'AWAITING_PAYMENT'  # Customer has completed the checkout process, but payment has yet to be confirmed. Authorize only transactions that are not yet captured have this status.
    STATUS_PENDING = 'PENDING'  # Customer finished checkout process and didn't have to pay for it, because total price = 0
    STATUS_PAYMENT_RECEIVED = 'PAYMENT_RECEIVED'  # Customer paid order and merchant received the successful transaction.
    STATUS_PROCESSING = 'PROCESSING'  # Customer paid order and merchant received the successful transaction.
    STATUS_AWAITING_FULFILLMENT = 'AWAITING_FULFILLMENT'  # Customer has completed the checkout process and payment has been confirmed.
    STATUS_AWAITING_SHIPMENT = 'AWAITING_SHIPMENT'  # Order has been pulled and packaged and is awaiting collection from a shipping provider.
    STATUS_AWAITING_PICKUP = 'AWAITING_PICKUP'  # Order has been packaged and is awaiting customer pickup from a seller-specified location.
    STATUS_PARTIALLY_SHIPPED = 'PARTIALLY_SHIPPED'  # Only some items in the order have been shipped, due to some products being pre-order only or other reasons.
    STATUS_SHIPPED = 'SHIPPED'  # Order has been shipped, but receipt has not been confirmed; seller has used the Ship Items action.
    STATUS_COMPLETED = 'COMPLETED'  # Order has been shipped/picked up, and receipt is confirmed; client has paid for their digital product, and their file(s) are available for download.
    STATUS_CANCELLED = 'CANCELLED'  # Seller has cancelled an order, due to a stock inconsistency or other reasons. Stock levels will automatically update depending on your Inventory Settings. Cancelling an order will not refund the order.
    STATUS_DECLINED = 'DECLINED'  # Seller has marked the order as declined for lack of manual payment, or other reasons
    STATUS_REFUNDED = 'REFUNDED'  # Seller has used the Refund action.
    STATUS_PARTIALLY_REFUNDED = 'PARTIALLY_REFUNDED'  # Seller has partially refunded the order.
    STATUS_DISPUTED = 'DISPUTED'  # Customer has initiated a dispute resolution process for the transaction that paid for the order.
    STATUS_ON_HOLD = 'ON_HOLD'  # Order on hold while some aspect (e.g. tax-exempt documentation) needs to be manually confirmed. Orders with this status must be updated manually. Capturing funds or other order actions will not automatically update the status of an order.

    STATUSES = [
        (STATUS_AWAITING_PAYMENT, _('Awaiting Payment')),
        (STATUS_PENDING, _('Pending')),
        (STATUS_PAYMENT_RECEIVED, _('Payment received')),
        (STATUS_PROCESSING, _('Processing')),
        (STATUS_AWAITING_FULFILLMENT, _('Awaiting Fulfillment')),
        (STATUS_AWAITING_SHIPMENT, _('Awaiting Shipment')),
        (STATUS_AWAITING_PICKUP, _('Awaiting Pickup')),
        (STATUS_PARTIALLY_SHIPPED, _('Partially Shipped')),
        (STATUS_SHIPPED, _('Shipped')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_CANCELLED, _('Cancelled')),
        (STATUS_DECLINED, _('Declined')),
        (STATUS_REFUNDED, _('Refunded')),
        (STATUS_PARTIALLY_REFUNDED, _('Partially Refunded')),
        (STATUS_DISPUTED, _('Disputed')),
        (STATUS_ON_HOLD, _('On hold')),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    status = models.CharField(_('status'), choices=STATUSES, max_length=20, db_index=True)
    number = models.PositiveSmallIntegerField(verbose_name=_('number'), db_index=True, unique=True)

    # delivery information
    delivery_name = models.CharField(_('full name or company name'), max_length=100, db_index=True)
    delivery_street = models.CharField(_('street and number'), max_length=200)
    delivery_postcode = models.CharField(_('postcode'), max_length=30)
    delivery_city = models.CharField(_('city'), max_length=50)
    delivery_country = CountryField(verbose_name=_('country'), db_index=True)

    # billing details
    billing_name = models.CharField(_('full name or company name'), max_length=100)
    billing_street = models.CharField(_('street'), max_length=200)
    billing_postcode = models.CharField(_('postcode'), max_length=30)
    billing_city = models.CharField(_('city'), max_length=50)
    billing_country = CountryField(verbose_name=_('country'), db_index=True)

    reg_id = models.CharField(_('Company Registration No.'), max_length=30, blank=True)
    tax_id = models.CharField(verbose_name=_('TAX ID'), max_length=30, blank=True)
    vat_id = VATNumberField(verbose_name=_('VAT ID'), blank=True)

    # Contact details
    email = models.EmailField(_('email'))
    phone = models.CharField(_('phone'), max_length=30, blank=True)

    # Shipping
    shipping_option = models.ForeignKey(ShippingOption, on_delete=models.PROTECT, null=True, default=None)
    shipping_fee = models.DecimalField(_('shipping fee'), help_text=commerce_settings.CURRENCY, max_digits=10, decimal_places=2, db_index=True, validators=[MinValueValidator(0)])

    # Payment method
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, null=True, default=None)
    payment_fee = models.DecimalField(_('payment fee'), help_text=commerce_settings.CURRENCY, max_digits=10, decimal_places=2, db_index=True, validators=[MinValueValidator(0)])

    # Invoices
    invoices = models.ManyToManyField(to='invoicing.Invoice', verbose_name=_('invoices'), blank=True, related_name='purchases')

    # Discount
    discount = models.ForeignKey(Discount, verbose_name=_('discount'), on_delete=models.PROTECT, blank=True, null=True, default=None)

    # Loyalty program
    loyalty_points = models.PositiveSmallIntegerField(_('loyalty points'), help_text=_('used to lower the total price'), blank=True, default=0)

    # Timestamps
    reminder_sent = models.DateTimeField(_('reminder sent'), blank=True, null=True, default=None)
    created = models.DateTimeField(_('created'), auto_now_add=True, db_index=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ('created',)

    def __str__(self):
        return str(self.number)

    @property
    def payment_manager(self):
        manager_class_path = commerce_settings.PAYMENT_MANAGERS.get(self.payment_method.method, None)

        if not manager_class_path:
            raise NotImplementedError()

        manager_class = import_string(manager_class_path)
        return manager_class(self)

    def get_absolute_url(self):
        # TODO
        # return reverse('commerce:order_detail', args=(self.number,))
        return reverse('commerce:orders')

    def get_payment_url(self):
        return reverse('commerce:order_payment', args=(self.number,))

    def get_payment_return_url(self):
        return reverse('commerce:order_payment_return', args=(self.number,))

    def get_payment_gateway_url(self):
        return self.payment_manager.get_payment_url()

    def render_payment_button(self):
        return self.payment_manager.render_payment_button()

    def render_payment_information(self):
        return self.payment_manager.render_payment_information()

    @property
    def loyalty_points_earned(self):
        if self not in self.user.order_set.with_earned_loyalty_points():
            return 0
        return currency_units_to_points(self.total)

    @property
    def loyalty_points_used(self):
        return self.loyalty_points

    def get_loyalty_points_display(self):
        return f'{self.loyalty_points} (-{points_to_currency_unit(self.loyalty_points)} {commerce_settings.CURRENCY})'

    @property
    def subtotal(self):
        subtotal = sum([item.subtotal for item in self.purchaseditem_set.all()])

        # discount
        if self.discount and self.discount.unit == Discount.UNIT_CURRENCY:
            subtotal -= self.discount.amount

        # loyalty program
        subtotal -= points_to_currency_unit(self.loyalty_points_used)

        return max(subtotal, 0)

    @property
    def total(self):
        total = self.subtotal
        total += self.shipping_fee
        total += self.payment_fee

        # Note: discount is already calculated in subtotal (item price)

        return total

    @property
    def total_in_cents(self):
        return int(self.total * 100)

    def get_total_display(self):
        return f'{self.total} {commerce_settings.CURRENCY}'

    @staticmethod
    def get_next_number():
        with transaction.atomic():
            Order.objects.lock()

            last_order = Order.objects.all().order_by('number').last()

            next_number = last_order.number + 1 if last_order else int(commerce_settings.ORDER_NUMBER_STARTS_FROM)

            # order number has to be unique
            while Order.objects.filter(number=next_number).exists():
                next_number += 1

            return next_number

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.number in EMPTY_VALUES:
            self.number = Order.get_next_number()

        return super().save(*args, **kwargs)

    def has_item_of_type(self, model):
        return self.items_of_type(model).exists()

    def items_of_type(self, model):
        return self.purchaseditem_set.filter(
            content_type=ContentType.objects.get_for_model(model),
        )

    def has_only_digital_goods(self):
        not_digital_goods = filter(
            lambda i: get_product_availability(i.product) != AbstractProduct.AVAILABILITY_DIGITAL_GOODS,
            self.purchaseditem_set.all()
        )
        return len(list(not_digital_goods)) == 0

    @property
    def delivery_details_required(self):
        return not self.has_only_digital_goods()

    def create_invoice(self, type=Invoice.TYPE.INVOICE, status=Invoice.STATUS.SENT):
        language = getattr(self.user, 'preferred_language', settings.LANGUAGE_CODE)  # TODO: user is Abstract model. preferred_language could be missing or should be configurable

        with override_language(language):
            issue_date = now().date()
            due_days = 0 if status == Invoice.STATUS.PAID else 7  # TODO: default due days
            delivery_method = Invoice.DELIVERY_METHOD.MAILING if self.delivery_details_required else Invoice.DELIVERY_METHOD.DIGITAL

            invoice = Invoice.objects.create(
                type=type,
                status=status,
                language=language,
                date_issue=issue_date,
                date_tax_point=issue_date,
                date_due=issue_date + relativedelta(days=due_days),
                currency=commerce_settings.CURRENCY,
                # already_paid=
                # payment_method=Invoice.PAYMENT_METHOD.BANK_TRANSFER,
                # payment_method=Invoice.PAYMENT_METHOD.BANK_TRANSFER if self.payment_method.method == Payment.METHOD_WIRE_TRANSFER
                # constant_symbol=
                variable_symbol=self.number,
                bank_name=settings.INVOICING_BANK['name'],
                bank_iban=settings.INVOICING_BANK['iban'],
                bank_swift_bic=settings.INVOICING_BANK['swift_bic'],
                supplier_name=settings.INVOICING_SUPPLIER['name'],
                supplier_street=settings.INVOICING_SUPPLIER['street'],
                supplier_zip=settings.INVOICING_SUPPLIER['zip'],
                supplier_city=settings.INVOICING_SUPPLIER['city'],
                supplier_country=settings.INVOICING_SUPPLIER['country_code'],
                supplier_registration_id=settings.INVOICING_SUPPLIER['registration_id'],
                supplier_tax_id=settings.INVOICING_SUPPLIER['tax_id'],
                supplier_vat_id=settings.INVOICING_SUPPLIER['vat_id'],
                # issuer_name
                issuer_email=settings.CONTACT_EMAIL,
                # issuer_phone
                customer_name=self.billing_name,
                customer_street=self.billing_street,
                customer_zip=self.billing_postcode,
                customer_city=self.billing_city,
                customer_country=self.billing_country,
                customer_registration_id=self.reg_id,
                customer_tax_id=self.tax_id,
                customer_vat_id=self.vat_id,
                customer_email=self.email,
                customer_phone=self.phone,
                shipping_name=self.delivery_name,
                shipping_street=self.delivery_street,
                shipping_zip=self.delivery_postcode,
                shipping_city=self.delivery_city,
                shipping_country=self.delivery_country,
                delivery_method=delivery_method
            )

            def check_tax_and_get_price(price, rate):
                if commerce_settings.UNIT_PRICE_IS_WITH_TAX and rate is not None and rate > 0:
                    return price / Decimal(100 + Decimal(rate)) * 100

                return price

            tax_rate = invoice.get_tax_rate()

            for purchaseditem in self.purchaseditem_set.all():
                item = InvoiceItem.objects.create(
                    invoice=invoice,
                    title=purchaseditem.title_with_option,
                    quantity=purchaseditem.quantity,
                    unit=InvoiceItem.UNIT_PIECES,
                    unit_price=check_tax_and_get_price(purchaseditem.price, tax_rate),
                    # discount=self.discount,  # TODO
                )

            # calculate credit (it's important to add it after items and invoice creation)
            credit = points_to_currency_unit(self.loyalty_points_used)

            if self.discount and self.discount.unit == Discount.UNIT_CURRENCY:
                credit += self.discount.amount

            # credit can't be more ten sum of items
            credit = min(credit, invoice.subtotal)

            # update invoice credit
            invoice.credit = credit
            invoice.save(update_fields=['credit'])

            shipping_fee = check_tax_and_get_price(self.shipping_fee, tax_rate)

            if shipping_fee > 0 and not commerce_settings.EXCLUDE_FREE_ITEMS_FROM_INVOICE:
                shipping_item = InvoiceItem.objects.create(
                    invoice=invoice,
                    title=_('Shipping fee'),
                    quantity=1,
                    unit=InvoiceItem.UNIT_EMPTY,
                    unit_price=shipping_fee,
                    # discount=self.discount,  # TODO
                )

            payment_fee = check_tax_and_get_price(self.payment_fee, tax_rate)

            if payment_fee > 0 and not commerce_settings.EXCLUDE_FREE_ITEMS_FROM_INVOICE:
                payment_item = InvoiceItem.objects.create(
                    invoice=invoice,
                    title=_('Payment fee'),
                    quantity=1,
                    unit=InvoiceItem.UNIT_EMPTY,
                    unit_price=payment_fee,
                    # discount=self.discount,  # TODO
                )

            self.invoices.add(invoice)

            # call custom signal
            invoice_created.send(sender=self.__class__, order=self, invoice=invoice)

            return invoice

    def send_details(self):
        with override_language(self.user.preferred_language):
            EmailManager.send_mail(self.user, 'commerce/mails/order_details', _('Order details: %d') % self.number, data={'order': self}, request=None)

    def send_reminder(self, force=False):
        if self.total <= 0:
            return

        if self.reminder_sent and not force:
            return

        with override_language(self.user.preferred_language):
            EmailManager.send_mail(self.user, 'commerce/mails/order_reminder', _('Order reminder: %d') % self.number, data={'order': self}, request=None)

        self.reminder_sent = now()
        self.save(update_fields=['reminder_sent'])


class PurchasedItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey('content_type', 'object_id')
    option = models.ForeignKey(Option, on_delete=models.PROTECT, blank=True, null=True, default=None)
    quantity = models.PositiveSmallIntegerField(verbose_name=_('quantity'))
    price = models.DecimalField(_('price'), help_text=commerce_settings.CURRENCY, max_digits=10, decimal_places=2, db_index=True, validators=[MinValueValidator(0)])
    files = models.ManyToManyField(to=File, verbose_name=_('files'), blank=True)
    created = models.DateTimeField(_('created'), auto_now_add=True, db_index=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    objects = PurchasedItemQuerySet.as_manager()

    class Meta:
        verbose_name = _('purchased item')
        verbose_name_plural = _('purchased items')

    def __str__(self):
        try:
            return str(self.product)
        except AttributeError:
            return 'Product deleted'

    @property
    def title_with_option(self):
        try:
            product_display = str(self.product)
        except AttributeError:
            product_display = 'Product deleted'

        return f'{product_display} ({self.option})' if self.option else product_display

    @property
    def subtotal(self):
        return self.quantity * self.price

    def get_subtotal_display(self):
        return f'{self.subtotal} {commerce_settings.CURRENCY}'

    def get_absolute_url(self):
        try:
            return self.product.get_absolute_url()
        except AttributeError:
            return None


class Supply(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey('content_type', 'object_id')  # does not work with parent class
    option = models.ForeignKey(Option, on_delete=models.PROTECT, blank=True, null=True, default=None)
    quantity = models.SmallIntegerField(verbose_name=_('quantity'), default=1)
    datetime = models.DateTimeField(_('datetime'))
    description = models.CharField(_('description'), max_length=50, blank=True)

    class Meta:
        verbose_name = _('supply')
        verbose_name_plural = _('supplies')
        ordering = ('datetime',)
        get_latest_by = 'datetime'

    @property
    def real_product(self):
        # print('real product is:')
        return self.content_type.get_object_for_this_type(id=self.object_id)

    def is_past_due(self):
        return self.datetime < now()

    def __str__(self):
        # print(self.content_type)
        # print(self.object_id)
        # print(self.product)
        # print(self.real_product)
        # return f'{self.product}: {self.quantity} [{self.datetime}]'
        return f'{self.real_product}: {self.quantity} [{self.datetime}]'


from .signals import *
