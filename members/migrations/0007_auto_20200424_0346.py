# Generated by Django 3.0.3 on 2020-04-24 01:46

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_auto_20200424_0345'),
    ]

    operations = [
        migrations.RenameField(
            model_name='session',
            old_name='website_titel',
            new_name='website_title',
        ),
        migrations.AlterField(
            model_name='event',
            name='end_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 24, 3, 46, 16, 738598)),
        ),
        migrations.AlterField(
            model_name='event',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 24, 3, 46, 16, 738580)),
        ),
        migrations.AlterField(
            model_name='session',
            name='end_time',
            field=models.TimeField(default=datetime.datetime(2020, 4, 24, 3, 46, 16, 738230)),
        ),
        migrations.AlterField(
            model_name='session',
            name='start_time',
            field=models.TimeField(default=datetime.datetime(2020, 4, 24, 3, 46, 16, 738207)),
        ),
    ]
