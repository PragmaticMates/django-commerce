# Generated by Django 2.2.4 on 2020-08-29 18:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0035_rename_models'),
        ('globalpayments', '0005_auto_20200828_1102'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Order',
            new_name='Payment',
        ),
    ]
