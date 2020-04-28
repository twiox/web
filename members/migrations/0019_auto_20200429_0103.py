# Generated by Django 3.0.3 on 2020-04-28 23:03

import datetime
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('members', '0018_auto_20200426_2227'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='trainer',
            options={'permissions': [('change_session', 'Einheit bearbeiten'), ('add_session', 'Einheit hinzufügen')]},
        ),
        migrations.AlterField(
            model_name='event',
            name='end_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 29, 1, 3, 24, 900661), verbose_name='Datum Ende'),
        ),
        migrations.AlterField(
            model_name='event',
            name='participants',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='event',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 29, 1, 3, 24, 900641), verbose_name='Datum Beginn'),
        ),
        migrations.AlterField(
            model_name='message',
            name='expire_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 29, 1, 3, 24, 904042)),
        ),
        migrations.AlterField(
            model_name='session',
            name='end_time',
            field=models.TimeField(default='19:00', verbose_name='Ende'),
        ),
        migrations.AlterField(
            model_name='session',
            name='start_time',
            field=models.TimeField(default='17:00', verbose_name='Beginn'),
        ),
    ]