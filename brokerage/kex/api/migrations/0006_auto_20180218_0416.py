# Generated by Django 2.0.2 on 2018-02-18 04:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_auto_20180218_0401'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='trades',
            field=models.ManyToManyField(blank=True, to='api.Trade'),
        ),
    ]