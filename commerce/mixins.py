from django.conf import settings
from django.utils.module_loading import import_string
from invoicing.taxation.eu import EUTaxationPolicy
from invoicing.models import default_supplier
from commerce import settings as commerce_settings


class TaxationMixin(object):

    @property
    def taxation_policy(self):
        taxation_policy = getattr(settings, 'INVOICING_TAXATION_POLICY', None)

        if taxation_policy is not None:
            return import_string(taxation_policy)

        supplier_country = default_supplier('country_code')
        if supplier_country and EUTaxationPolicy.is_in_EU(supplier_country):
            return EUTaxationPolicy

        return None

    @property
    def total(self):
        total = self.subtotal
        total += self.shipping_fee if hasattr(self, 'shipping_fee') else 0
        total += self.payment_fee if hasattr(self, 'payment_fee') else 0

        if not commerce_settings.UNIT_PRICE_IS_WITH_TAX and self.taxation_policy and default_supplier('vat_id') and total > 0:
            tax_rate = self.taxation_policy.get_tax_rate(default_supplier('vat_id'), self.vat_id)
            total += round(self.taxation_policy.calculate_tax(total, tax_rate), 2)

            # Note: discount is already calculated in subtotal (item price)

        return total

    def get_total_display(self):
        return f'{self.total} {commerce_settings.CURRENCY}'

    @property
    def vat(self):
        if not commerce_settings.UNIT_PRICE_IS_WITH_TAX and self.taxation_policy and default_supplier('vat_id'):
            tax_rate = self.taxation_policy.get_tax_rate(default_supplier('vat_id'), self.vat_id)
            return round(self.taxation_policy.calculate_tax(self.total, tax_rate), 2)

        return None

    def get_vat_display(self):
        return f'{self.vat} {commerce_settings.CURRENCY}'