# Generated by Django 5.0.7 on 2024-07-29 18:09

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LinkChecker', '0004_rename_recheckintervaldays_globals_checkallintervalmins_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='links_table',
            name='brokenSince',
            field=models.DateTimeField(default=datetime.datetime(2024, 7, 29, 11, 9, 46, 892060)),
        ),
    ]