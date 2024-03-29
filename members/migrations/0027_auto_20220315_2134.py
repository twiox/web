# Generated by Django 3.0.3 on 2022-03-15 21:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0026_gallery_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='title',
            field=models.CharField(blank=True, max_length=200, verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='gallery',
            name='title',
            field=models.CharField(blank=True, max_length=200, verbose_name='Title'),
        ),
        migrations.CreateModel(
            name='ShopItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=300, verbose_name='Title')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('description_rendered', models.TextField(blank=True, null=True)),
                ('gallery', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='members.Gallery')),
            ],
        ),
    ]
