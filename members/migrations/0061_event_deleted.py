# Generated by Django 3.0.3 on 2024-03-15 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0060_profile_permission_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='deleted',
            field=models.BooleanField(default=False, verbose_name='Gelöscht'),
        ),
    ]
