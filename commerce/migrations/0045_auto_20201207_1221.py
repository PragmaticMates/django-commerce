# Generated by Django 2.2.9 on 2020-12-07 11:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0044_auto_20201207_1215'),
    ]

    operations = [
        migrations.AddField(
            model_name='supply',
            name='description',
            field=models.CharField(blank=True, max_length=50, verbose_name='description'),
        ),
    ]
