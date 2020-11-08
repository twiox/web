# Generated by Django 3.0.3 on 2020-11-02 17:49

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0010_auto_20201029_0242'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='deadline',
            field=models.DateTimeField(default=datetime.datetime(2020, 11, 2, 18, 49, 50, 776331), verbose_name='Anmeldung/Abmeldung bis'),
        ),
        migrations.AlterField(
            model_name='event',
            name='end_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 11, 2, 18, 49, 50, 776382), verbose_name='Datum Ende'),
        ),
        migrations.AlterField(
            model_name='event',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 11, 2, 18, 49, 50, 776370), verbose_name='Datum Beginn'),
        ),
        migrations.AlterField(
            model_name='message',
            name='date',
            field=models.DateTimeField(default=datetime.datetime(2020, 11, 2, 18, 49, 50, 779882)),
        ),
    ]
