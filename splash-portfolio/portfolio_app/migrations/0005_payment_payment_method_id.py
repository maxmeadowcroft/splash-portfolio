# Generated by Django 5.1.3 on 2024-12-03 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio_app', '0004_payment_card_last4_payment_card_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='payment_method_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
