# Generated by Django 5.1.3 on 2024-12-02 20:13

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio_app', '0002_customuser_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='renewal_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
