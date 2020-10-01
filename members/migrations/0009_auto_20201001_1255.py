# Generated by Django 3.0.3 on 2020-10-01 10:55

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0008_auto_20200930_1239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='deadline',
            field=models.DateTimeField(default=datetime.datetime(2020, 10, 1, 12, 55, 44, 166439), verbose_name='Anmeldung/Abmeldung bis'),
        ),
        migrations.AlterField(
            model_name='event',
            name='end_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 10, 1, 12, 55, 44, 166470), verbose_name='Datum Ende'),
        ),
        migrations.AlterField(
            model_name='event',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2020, 10, 1, 12, 55, 44, 166458), verbose_name='Datum Beginn'),
        ),
        migrations.AlterField(
            model_name='message',
            name='date',
            field=models.DateTimeField(default=datetime.datetime(2020, 10, 1, 12, 55, 44, 169667)),
        ),
        migrations.AlterField(
            model_name='profile',
            name='status',
            field=models.CharField(choices=[('Ordentliches Mitglied', 'Ordentliches Mitglied'), ('Förderndes Mitglied', 'Förderndes Mitglied'), ('Pausiertes Mitglied', 'Pausiertes Mitglied'), ('Kündigung', 'Kündigung')], default='Ordentliches Mitglied', max_length=40),
        ),
        migrations.AlterField(
            model_name='profile',
            name='zahlungsart',
            field=models.CharField(choices=[('SEPA', 'SEPA'), ('Dauerauftrag', 'Dauerauftrag'), ('Überweisung', 'Überweisung')], default='SEPA', max_length=30, verbose_name='Zahlungsart'),
        ),
        migrations.DeleteModel(
            name='Participant',
        ),
    ]
