# Generated by Django 2.2.4 on 2020-11-13 16:24

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('commerce', '0039_auto_20201022_2054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='phone',
            field=models.CharField(blank=True, max_length=30, verbose_name='phone'),
        )
    ]