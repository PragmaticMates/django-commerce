# Generated by Django 2.2.4 on 2020-07-14 19:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0028_auto_20200710_1214'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='reminder_sent',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='reminder sent'),
        ),
    ]
