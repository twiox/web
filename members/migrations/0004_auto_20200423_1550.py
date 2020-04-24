# Generated by Django 3.0.3 on 2020-04-23 13:50

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0003_auto_20200422_1703'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='members.Group'),
        ),
        migrations.AddField(
            model_name='profile',
            name='member_num',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='profile',
            name='nickname',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='profile',
            name='status',
            field=models.CharField(choices=[('aktiv', 'Aktiv'), ('fördernd', 'Fördernd'), ('kündigung', 'Kündigung'), ('pausiert', 'Pausiert')], default='aktiv', max_length=30),
        ),
        migrations.AddField(
            model_name='profile',
            name='telnr',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='event',
            name='end_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 23, 15, 50, 37, 10984)),
        ),
        migrations.AlterField(
            model_name='event',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 4, 23, 15, 50, 37, 10967)),
        ),
        migrations.AlterField(
            model_name='session',
            name='end_time',
            field=models.TimeField(default=datetime.datetime(2020, 4, 23, 15, 50, 37, 10628)),
        ),
        migrations.AlterField(
            model_name='session',
            name='start_time',
            field=models.TimeField(default=datetime.datetime(2020, 4, 23, 15, 50, 37, 10605)),
        ),
    ]
