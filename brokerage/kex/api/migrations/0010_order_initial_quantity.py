# Generated by Django 2.0.2 on 2018-05-17 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_auto_20180218_0713'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='initial_quantity',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
