from django.contrib.auth.models import Permission

# codename fragments, e.g. "session" covers add/change/delete/view_session


def trainer_permissions():
    all_perms = []
    for model in ["spot", "event", "session", "message"]:
        all_perms.extend(Permission.objects.filter(codename__contains=model))
    return all_perms


def chairman_permissions():
    all_perms = trainer_permissions()
    for model in ["user", "chairman", "trainer", "teamer"]:
        all_perms.extend(Permission.objects.filter(codename__contains=model))
    return all_perms
