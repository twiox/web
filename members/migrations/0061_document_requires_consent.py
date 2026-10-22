from django.db import migrations, models

# the documents the old sign-up page asked to accept
CONSENT_NAMES = ["Teilnahmebedingungen", "Datenschutzerklärung", "Einverständniserklärung"]


def mark_consent_documents(apps, schema_editor):
    Document = apps.get_model("members", "Document")
    Document.objects.filter(name__in=CONSENT_NAMES).update(requires_consent=True)


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0060_event_documents_to_orga"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="requires_consent",
            field=models.BooleanField(default=False, verbose_name="Muss bei der Anmeldung bestätigt werden"),
        ),
        migrations.RunPython(mark_consent_documents, migrations.RunPython.noop),
    ]
