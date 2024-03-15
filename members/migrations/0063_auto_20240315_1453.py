# Generated by Django 3.0.3 on 2024-03-15 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0062_auto_20240315_1125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chairman',
            name='image',
            field=models.ImageField(upload_to='uploads/chairmen/profile_pics/', verbose_name='Profilbild'),
        ),
        migrations.AlterField(
            model_name='descriptionimage',
            name='image',
            field=models.ImageField(upload_to='uploads/descriptions/images/', verbose_name='Foto'),
        ),
        migrations.AlterField(
            model_name='document',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='uploads/events/docs', verbose_name='File'),
        ),
        migrations.AlterField(
            model_name='event',
            name='datenschutz',
            field=models.FileField(blank=True, null=True, upload_to='uploads/events/docs', verbose_name='Datenschutzerklärung'),
        ),
        migrations.AlterField(
            model_name='event',
            name='einverstaendnis',
            field=models.FileField(blank=True, null=True, upload_to='uploads/events/docs', verbose_name='Einverständniserklärung'),
        ),
        migrations.AlterField(
            model_name='event',
            name='teilnahmebedingungen',
            field=models.FileField(blank=True, null=True, upload_to='uploads/events/docs/', verbose_name='Teilnahmebedingungen'),
        ),
        migrations.AlterField(
            model_name='news',
            name='picture',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/news/images', verbose_name='Stockphoto'),
        ),
        migrations.AlterField(
            model_name='trainer',
            name='codex',
            field=models.FileField(blank=True, null=True, upload_to='uploads/trainer/docs', verbose_name='Ehrencodex'),
        ),
        migrations.AlterField(
            model_name='trainer',
            name='contract',
            field=models.FileField(blank=True, null=True, upload_to='uploads/trainer/docs', verbose_name='Vertrag'),
        ),
        migrations.AlterField(
            model_name='trainer',
            name='image',
            field=models.ImageField(upload_to='uploads/trainer/profile_pics/', verbose_name='Profilbild'),
        ),
        migrations.AlterField(
            model_name='trainer',
            name='license',
            field=models.FileField(blank=True, null=True, upload_to='uploads/trainer/docs', verbose_name='Lizenz'),
        ),
    ]
