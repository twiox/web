# Generated by Django 3.0.3 on 2023-01-08 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0040_auto_20230108_0304'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='autodelete',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Automatisches Löschen'),
        ),
    ]
