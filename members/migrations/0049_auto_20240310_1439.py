# Generated by Django 3.0.3 on 2024-03-10 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0048_auto_20240310_1421'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='participant',
            name='has_ticket',
        ),
        migrations.AddField(
            model_name='participant',
            name='fields',
            field=models.TextField(blank=True, null=True, verbose_name='Formfelder'),
        ),
    ]
