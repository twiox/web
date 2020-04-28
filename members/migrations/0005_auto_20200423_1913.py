# Generated by Django 3.0.3 on 2020-04-23 17:13

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0004_auto_20200423_1550'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='nickname',
        ),
        migrations.AlterField(
            model_name='event',
            name='end_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 23, 19, 13, 27, 356598)),
        ),
        migrations.AlterField(
            model_name='event',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 23, 19, 13, 27, 356583)),
        ),
        migrations.AlterField(
            model_name='session',
            name='end_time',
            field=models.TimeField(default=datetime.datetime(2020, 4, 23, 19, 13, 27, 356246)),
        ),
        migrations.AlterField(
            model_name='session',
            name='start_time',
            field=models.TimeField(default=datetime.datetime(2020, 4, 23, 19, 13, 27, 356219)),
        ),
    ]