# Generated by Django 5.1.3 on 2024-12-02 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio_app', '0003_payment_renewal_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='card_last4',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='card_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
