# Generated by Django 5.0 on 2023-12-26 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0003_transaction_account_no_transaction_is_bankrupt_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='account_no',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]