# Generated by Django 3.0.3 on 2022-03-20 18:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0025_auto_20220104_0034'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='costs',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True, verbose_name='Kosten'),
        ),
    ]
