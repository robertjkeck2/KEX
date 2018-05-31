# Generated by Django 2.0.2 on 2018-02-16 21:08

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('account_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('phone_number', models.CharField(max_length=15, unique=True, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+999999999'.         Up to 15 digits allowed.", regex='^\\+?1?\\d{9,15}$')])),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('order_id', models.CharField(max_length=500, primary_key=True, serialize=False)),
                ('side', models.CharField(max_length=4)),
                ('order_type', models.CharField(max_length=6)),
                ('symbol', models.CharField(max_length=10)),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10)),
                ('quantity', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_updated_at', models.DateTimeField(blank=True, null=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Account')),
            ],
        ),
        migrations.CreateModel(
            name='Price',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('best_ask', models.DecimalField(blank=True, decimal_places=2, max_digits=10)),
                ('best_bid', models.DecimalField(blank=True, decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='Trade',
            fields=[
                ('trade_id', models.CharField(max_length=500, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField()),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10)),
                ('symbol', models.CharField(max_length=10)),
                ('quantity', models.IntegerField()),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buyer_account', to='api.Account')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_account', to='api.Account')),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='trades',
            field=models.ManyToManyField(to='api.Trade'),
        ),
    ]