# Generated by Django 3.0.3 on 2020-04-22 15:03

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0002_auto_20200422_1701'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='end_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 22, 17, 3, 32, 785994)),
        ),
        migrations.AlterField(
            model_name='event',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 22, 17, 3, 32, 785949)),
        ),
        migrations.AlterField(
            model_name='session',
            name='end_time',
            field=models.TimeField(default=datetime.datetime(2020, 4, 22, 17, 3, 32, 785640)),
        ),
        migrations.AlterField(
            model_name='session',
            name='start_time',
            field=models.TimeField(default=datetime.datetime(2020, 4, 22, 17, 3, 32, 785619)),
        ),
    ]
