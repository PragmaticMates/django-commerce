# Generated by Django 2.2.4 on 2020-06-25 17:40

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0003_auto_20200625_1936'),
    ]

    operations = [
        migrations.RenameField(
            model_name='shipping',
            old_name='price',
            new_name='fee',
        ),
    ]
