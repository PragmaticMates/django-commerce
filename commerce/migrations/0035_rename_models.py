# Generated by Django 2.2.4 on 2020-08-29 18:12

import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0034_auto_20200823_1233'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Payment',
            new_name='PaymentMethod',
        ),
        migrations.RenameModel(
            old_name='Shipping',
            new_name='ShippingOption',
        ),
        migrations.RemoveIndex(
            model_name='paymentmethod',
            name='commerce_pa_i18n_b04da9_gin',
        ),
        migrations.RemoveIndex(
            model_name='shippingoption',
            name='commerce_sh_i18n_34b55b_gin',
        ),
        migrations.AddIndex(
            model_name='paymentmethod',
            index=django.contrib.postgres.indexes.GinIndex(fields=['i18n'], name='commerce_pa_i18n_f82725_gin'),
        ),
        migrations.AddIndex(
            model_name='shippingoption',
            index=django.contrib.postgres.indexes.GinIndex(fields=['i18n'], name='commerce_sh_i18n_a10d2b_gin'),
        ),

        # TODO:
        # alter table commerce_paymentmethod_shippings rename column shipping_id to shippingoption_id
    ]
