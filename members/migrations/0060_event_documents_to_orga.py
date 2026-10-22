from django.db import migrations

# the fixed upload fields of the event form; from now on documents are managed on the orga page
FIELDS = [
    ("teilnahmebedingungen", "Teilnahmebedingungen"),
    ("datenschutz", "Datenschutzerklärung"),
    ("einverstaendnis", "Einverständniserklärung"),
]


def fields_to_documents(apps, schema_editor):
    Event = apps.get_model("members", "Event")
    Document = apps.get_model("members", "Document")
    for event in Event.objects.all():
        for field, name in FIELDS:
            file = getattr(event, field)
            if file:
                # same stored file, now as a public document of the event
                Document.objects.create(name=name, file=file.name, event_public=event)


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0059_participant_responsible"),
    ]

    operations = [
        migrations.RunPython(fields_to_documents, migrations.RunPython.noop),
        migrations.RemoveField(model_name="event", name="teilnahmebedingungen"),
        migrations.RemoveField(model_name="event", name="datenschutz"),
        migrations.RemoveField(model_name="event", name="einverstaendnis"),
    ]
