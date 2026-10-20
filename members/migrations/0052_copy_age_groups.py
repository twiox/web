from django.db import migrations


def age_range(agegroups):
    """Combined range of the age groups; 0 and 99 (the old defaults) mean no limit."""
    agegroups = list(agegroups)
    if not agegroups:
        return None, None
    lower = min(group.lower for group in agegroups)
    upper = max(group.upper for group in agegroups)
    return (lower or None), (upper if upper < 99 else None)


def copy_age_groups(apps, schema_editor):
    Event = apps.get_model("members", "Event")
    Session = apps.get_model("members", "Session")
    Message = apps.get_model("members", "Message")

    for event in Event.objects.prefetch_related("allowed_agegroups"):
        event.min_age, event.max_age = age_range(event.allowed_agegroups.all())
        event.save(update_fields=["min_age", "max_age"])

    for session in Session.objects.select_related("agegroup"):
        session.min_age, session.max_age = age_range([session.agegroup] if session.agegroup else [])
        session.save(update_fields=["min_age", "max_age"])

    # a message for an age group now belongs to the sessions of that age group
    for message in Message.objects.prefetch_related("agegroup"):
        message.sessions.set(Session.objects.filter(agegroup__in=message.agegroup.all()))


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0051_age_range_fields"),
    ]

    operations = [
        migrations.RunPython(copy_age_groups, migrations.RunPython.noop),
    ]
