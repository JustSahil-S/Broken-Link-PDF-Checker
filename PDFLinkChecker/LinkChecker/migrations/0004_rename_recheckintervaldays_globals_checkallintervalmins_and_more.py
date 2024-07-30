# Generated by Django 5.0.7 on 2024-07-29 16:18

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LinkChecker', '0003_alter_globals_checkallnextat_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='globals',
            old_name='recheckIntervalDays',
            new_name='checkAllIntervalMins',
        ),
        migrations.RenameField(
            model_name='globals',
            old_name='recheckIntervalHours',
            new_name='checkAllStartAtMin',
        ),
        migrations.RemoveField(
            model_name='globals',
            name='checkAllNextAt',
        ),
        migrations.RemoveField(
            model_name='globals',
            name='recheckIntervalMins',
        ),
        migrations.AddField(
            model_name='globals',
            name='checkAllIntervalHours',
            field=models.IntegerField(default=24),
        ),
        migrations.AddField(
            model_name='globals',
            name='checkAllStartAtHour',
            field=models.IntegerField(default=7),
        ),
        migrations.AlterField(
            model_name='links_table',
            name='brokenSince',
            field=models.DateTimeField(default=datetime.datetime(2024, 7, 29, 9, 18, 1, 236659)),
        ),
    ]