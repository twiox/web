from django.db import migrations, models


def file_to_flag(apps, schema_editor):
    # a stored consent form means the consent is there; the files themselves are no longer kept
    Tester = apps.get_model("interested", "Tester")
    Tester.objects.exclude(einverstaendnis="").exclude(einverstaendnis__isnull=True).update(has_consent=True)


def unknown_sign_up_date(apps, schema_editor):
    # Django fills auto_now_add with the migration time; for older sign-ups the real date is unknown
    apps.get_model("interested", "Tester").objects.update(created=None)


class Migration(migrations.Migration):

    dependencies = [
        ("interested", "0023_eventparticipant_inform_ok"),
    ]

    operations = [
        migrations.AddField(
            model_name="tester",
            name="has_consent",
            field=models.BooleanField(default=False, verbose_name="Einverständniserklärung liegt vor"),
        ),
        migrations.RunPython(file_to_flag, migrations.RunPython.noop),
        migrations.RemoveField(model_name="tester", name="einverstaendnis"),
        migrations.AddField(
            model_name="tester",
            name="created",
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name="Anfrage vom"),
        ),
        migrations.RunPython(unknown_sign_up_date, migrations.RunPython.noop),
    ]
