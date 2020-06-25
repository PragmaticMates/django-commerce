# Generated by Django 2.2.4 on 2020-06-25 17:33

import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shipping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50, verbose_name='title')),
                ('price', models.DecimalField(blank=True, db_index=True, decimal_places=2, default=None, help_text='EUR', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='price')),
                ('countries', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=2, verbose_name='country'), blank=True, default=list, size=50, verbose_name='countries')),
            ],
            options={
                'verbose_name': 'shipping',
                'verbose_name_plural': 'shippings',
            },
        ),
    ]
