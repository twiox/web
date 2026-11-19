"""The permission groups "Trainer" and "Vorstand" are gone: access follows the roles in
members/roles.py (Trainer.active, Chairman.active), not Django permissions."""
from django.db import migrations

ROLE_GROUPS = ["Trainer", "Vorstand"]


def remove_groups(apps, schema_editor):
    # deleting a group also removes its memberships and permission links
    apps.get_model("auth", "Group").objects.filter(name__in=ROLE_GROUPS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0062_participant_checked_in"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    # going back leaves them out: nothing reads them anymore
    operations = [migrations.RunPython(remove_groups, migrations.RunPython.noop)]
