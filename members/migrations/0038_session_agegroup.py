# Generated by Django 3.0.3 on 2023-01-07 20:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0037_auto_20230107_1933'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='agegroup',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='agegroup', to='members.AgeGroup', verbose_name='Altersgruppe'),
        ),
    ]
