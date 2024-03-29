# Generated by Django 3.0.3 on 2022-03-20 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0026_auto_20220320_1848'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='deadline',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Anmeldung/Abmeldung bis'),
        ),
        migrations.AlterField(
            model_name='event',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Datum Ende'),
        ),
        migrations.AlterField(
            model_name='event',
            name='start_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Datum Beginn'),
        ),
    ]
