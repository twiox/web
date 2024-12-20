# Generated by Django 5.1 on 2024-08-26 20:38

import multiselectfield.db.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0044_memberparticipant_has_ticket"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chairman",
            name="show",
            field=multiselectfield.db.fields.MultiSelectField(
                blank=True,
                choices=[
                    ("member_site", "Anzeige Mitglieder"),
                    ("interested_site", "Anzeige Interessierte"),
                    ("event_site", "Anzeige Veranstalter"),
                    ("interested_xdream", "Anzeige XDream"),
                ],
                max_length=300,
            ),
        ),
    ]
