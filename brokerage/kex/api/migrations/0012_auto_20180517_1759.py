# Generated by Django 2.0.2 on 2018-05-17 17:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_auto_20180517_1537'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='last_updated_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
