from django.db.models.signals import post_save, post_delete, post_migrate, pre_delete
from django.contrib.auth.models import User
from django.contrib.auth.models import Group as PermissionGroup
from django.dispatch import receiver
from members.models import Profile, Trainer, Chairman
from interested.models import Tester
from interested.trials import mark_member
from trainer.models import TrainingSessionParticipant
from .permissions import trainer_permissions, chairman_permissions


# every user has a profile; code that changes user.profile and then saves the
# user relies on the profile being saved along with it
@receiver(post_save, sender=User)
def create_or_save_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


# a new (or corrected) member who did a trial training: their request is done.
# Saving the user saves the profile too (above), so name changes land here as well.
@receiver(post_save, sender=Profile)
def mark_trial_member(sender, instance, **kwargs):
    mark_member(instance.user.first_name, instance.user.last_name, instance.birthday)


# a deleted trial request: the training sessions keep the attendance (for the participant
# count), but not the copied name and notes, which nothing would link to anymore
@receiver(pre_delete, sender=Tester)
def anonymise_trial_attendance(sender, instance, **kwargs):
    TrainingSessionParticipant.objects.filter(tester=instance).update(name="Probetraining (gelöscht)", notes=None)


# Trainer and chairman rights come from these permission groups. Syncing them in
# signals keeps the rights right no matter how a role is switched on or off
# (our views, the Django admin, or deleting the user).
ROLE_GROUPS = {Trainer: "Trainer", Chairman: "Vorstand"}


@receiver(post_save, sender=Trainer)
@receiver(post_save, sender=Chairman)
def sync_role_permissions(sender, instance, **kwargs):
    group = PermissionGroup.objects.get(name=ROLE_GROUPS[sender])
    if instance.active:
        group.user_set.add(instance.user)
    else:
        group.user_set.remove(instance.user)
        if sender is Trainer:
            # leaves the weekly schedule; past session entries and invoices keep the trainer
            instance.session_set.clear()


@receiver(post_delete, sender=Trainer)
@receiver(post_delete, sender=Chairman)
def revoke_role_permissions(sender, instance, **kwargs):
    PermissionGroup.objects.get(name=ROLE_GROUPS[sender]).user_set.remove(instance.user_id)


@receiver(post_migrate)
def sync_role_group_permissions(sender, **kwargs):
    # Django creates permissions app by app during post_migrate, so this runs for every
    # app and the last run sees all of them; permissions.py is the source of truth
    for group_name, permissions in [("Trainer", trainer_permissions()), ("Vorstand", chairman_permissions())]:
        group, _ = PermissionGroup.objects.get_or_create(name=group_name)
        group.permissions.set(permissions)
