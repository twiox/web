from django.db import migrations

ROLE_GROUPS = {"Trainer": "Trainer", "Chairman": "Vorstand"}


def add_existing_roles(apps, schema_editor):
    # the permissions themselves are set by the post_migrate hook in user_handling/signals.py
    PermissionGroup = apps.get_model("auth", "Group")
    for model_name, group_name in ROLE_GROUPS.items():
        group, _ = PermissionGroup.objects.get_or_create(name=group_name)
        model = apps.get_model("members", model_name)
        group.user_set.add(*model.objects.values_list("user_id", flat=True))


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0048_optional_role_profile"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(add_existing_roles, migrations.RunPython.noop),
    ]
