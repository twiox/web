# Generated by Django 3.0.3 on 2022-03-15 22:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0030_auto_20220315_2246'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shopitem',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, verbose_name='Price'),
        ),
    ]
