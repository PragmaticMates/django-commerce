# Generated by Django 2.2.4 on 2020-11-30 21:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('commerce', '0042_auto_20201130_2222'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discount',
            name='content_types',
            field=models.ManyToManyField(blank=True, to='contenttypes.ContentType', verbose_name='content types'),
        ),
    ]