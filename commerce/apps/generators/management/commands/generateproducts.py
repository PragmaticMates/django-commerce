# -*- coding: utf-8

from random import choice

from django.core.management.base import BaseCommand, CommandError

from commerce.models.catalog import Catalog
from commerce.models.product import Product
from commerce.models.manufacturer import Manufacturer


class Command(BaseCommand):
    PRICES = (76.99, 53.99, 44.99, 7.99, 99.99, 120.00, 999.99)

    TOP = (False, False, False, False, False, False, True)

    NEW = (False, False, False, False, False, False, True)

    DISCOUNT = (False, False, False, True)

    COVERS = (
        'commerce/products/covers/examples/product-example1.jpg',
        'commerce/products/covers/examples/product-example2.jpg',
        'commerce/products/covers/examples/product-example3.jpg',
        'commerce/products/covers/examples/product-example4.jpg',
        'commerce/products/covers/examples/product-example5.jpg',
        'commerce/products/covers/examples/product-example6.jpg',
        'commerce/products/covers/examples/product-example7.jpg',
        'commerce/products/covers/examples/product-example8.jpg',
        'commerce/products/covers/examples/product-example9.jpg',
        'commerce/products/covers/examples/product-example10.jpg',
        'commerce/products/covers/examples/product-example11.jpg',
        'commerce/products/covers/examples/product-example12.jpg',
        'commerce/products/covers/examples/product-example13.jpg',
    )

    TITLES = (
        'BPI SPORTS BUILD-HD™',
        'THE ORIGINAL Colon Cleanse®',
        'Fiber Soft Chews',
        'Unflavored',
        'Clear Mixing Super Fiber with Probiotics',
        'Psyllium Seed Husk',
        'Clear Mixing Super Fiber',
        'Colon Care Formula',
        'Super Colon Cleanse®',
        'BIORhythm Slim to None',
    )

    SUBPRODUCTS_TITLES = (
        'Cherry', 'Peach', 'Strawberry', 'Chocolate', 'Vanilla', 'Pear',
        'Watermelon', 'Banana', 'Kiwi', 'Apple', 'Wine',
    )
    DESCRIPTIONS = (
        '<ul><li>The colon is responsible for the final stages of digestion.\
        </li><li>Colon Care combines plant based fiber from 400 mg of \
        psyllium seed husk, 200 mg oat bran and 200 mg of wheat bran to help \
        maintain a healthy digestive tract and 500 mg FOS to help acidophilus \
        flourish in the intestines</li>',
        '<p>Delicious Multi-Fruit Flavor</p><p>Enjoy a great tasting way to \
        supplement your daily fiber intake now with Garden Greens™ Fiber \
        Gummies with Probiotics. Fiber Gummies are a breakthrough in the \
        way that people can supplement their daily fiber intake. These \
        gummies are a chewable-functional confectionary product that are \
        designed to make taking supplements easier and enjoyable.</p><p>Apart\
         from providing you with your daily fiber intake, Garden Greens™ \
         Fiber Gummies eliminates the much averse task of swallowing the \
         conventional fiber pills. Two delicious gummies per day provides \
         5 grams of fiber with 4 calories per serving.</p><p>Garden Greens™ \
         Fiber Gummies formulated with high quality chicory root combined \
         with a high fiber diet will help promote a healthy lifestyle. \
         Garden Greens™ Fiber Gummies is a great-tasting, convenient way to \
         supplement your daily fiber intake to support regularity.</p>',
        '<p>Highly Effective Whey-Leucine Base - The impressive 60 grams of \
        protein is made entirely from the highest quality, fast-absorbing \
        forms of whey protein - isolates and hydrolysates. With 7.7 grams of \
        leucine, this creates an ideal environment for muscle protein \
        synthesis. This potent blend upregulates multiple Genetic Signaling \
        Pathways (GSP) to enhance anabolism and muscle performance.* In fact,\
         the whey and leucine blend in Amplified Wheybolic Extreme 60™ has \
         been shown to increase muscle strength and stamina with half the \
         sets.*</p><p>Micronized Amino Acids - Using MicroSorb™ Amino \
         Technology, the amino acids added to this formula are pulverized, \
         or "micronized" from large molecules into smaller particles to \
         facilitate faster absorption. Why is that important? Better \
         absorption of amino acids means better muscle fuel. \
         These key amino acids support muscle building and \
         recovery.*</p><p>Amino Acceleration System - This digestive enzyme \
         blend is designed to accelerate the availability and absorption of \
         amino acids to be efficiently used by the muscles.</p>',
    )

    manufacturers = Manufacturer.objects.all().values_list('pk', flat=True)
    catalogs = Catalog.objects.all().values_list('pk', flat=True)

    def handle(self, *args, **options):
        try:
            products_to_generate = int(args[0])
        except IndexError:
            products_to_generate = 100

        if len(self.catalogs) is None:
            raise CommandError('No catalogs found.\
             Please create some catalogs.')

        for index in range(products_to_generate):
            product = self._random_product()
            for index in range(choice(range(50))):
                self._random_product(product)

    def _random_product(self, associated_product=None):
        # Manufacturer
        if len(self.manufacturers) is 0:
            manufacturer = None
        elif associated_product is not None:
            manufacturer = associated_product.manufacturer_id
        else:
            manufacturer = choice(self.manufacturers)

        # Catalog
        if associated_product is not None:
            catalog_id = associated_product.catalog_id
        else:
            catalog_id = choice(self.catalogs)

        # Prices
        price = choice(self.PRICES)
        is_discount = choice(self.DISCOUNT)
        price_common = choice(range(int(price)))

        price_discount = None
        price_real = price

        if is_discount:
            price_discount = price - (price / 100 * choice(range(99)))
            price_real = price_discount

        product = Product.objects.create(
            associated_product=associated_product,
            manufacturer_id=manufacturer,
            catalog_id=catalog_id,
            title=choice(self.TITLES),
            description=choice(self.DESCRIPTIONS),
            price=price,
            price_common=price_common,
            price_discount=price_discount,
            price_real=price_real,
            cover=choice(self.COVERS),
            is_new=choice(self.NEW),
            is_top=choice(self.TOP),
            file='commerce/products/files/examples/example.pdf',
        )
        product.slug = 'product-' + str(product.pk)
        product.save()
        return product
