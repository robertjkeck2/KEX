# Generated by Django 2.0.2 on 2018-02-18 05:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_auto_20180218_0416'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='api_key',
        ),
    ]
