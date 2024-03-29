# Generated by Django 3.0.3 on 2023-03-12 11:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interested', '0018_auto_20220803_0354'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tester',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=400, verbose_name='Vorname')),
                ('last_name', models.CharField(max_length=400, verbose_name='Nachname')),
                ('email', models.CharField(max_length=300, verbose_name='Email')),
                ('birthday', models.DateTimeField(verbose_name='Geburtstag')),
                ('telnr', models.CharField(blank=True, max_length=300, null=True, verbose_name='Telefonnummer')),
                ('sex', models.CharField(max_length=30, verbose_name='Geschlecht')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Anmerkungen')),
            ],
        ),
    ]
