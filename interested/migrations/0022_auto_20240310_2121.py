# Generated by Django 3.0.3 on 2024-03-10 21:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('interested', '0021_auto_20230321_1016'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ContactPerson',
        ),
        migrations.RemoveField(
            model_name='eventmerch',
            name='event',
        ),
        migrations.RemoveField(
            model_name='eventparticipant',
            name='event',
        ),
        migrations.RemoveField(
            model_name='publiceventparticipantmerch',
            name='merch',
        ),
        migrations.RemoveField(
            model_name='publiceventparticipantmerch',
            name='participant',
        ),
        migrations.DeleteModel(
            name='Teamer',
        ),
        migrations.DeleteModel(
            name='EventMerch',
        ),
        migrations.DeleteModel(
            name='EventParticipant',
        ),
        migrations.DeleteModel(
            name='PublicEvent',
        ),
        migrations.DeleteModel(
            name='PublicEventParticipantMerch',
        ),
    ]