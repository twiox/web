from django.db.models.signals import post_save, pre_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from members.models import Profile
from public.models import Tester
from public.trials import mark_member
from trainer.models import TrainingSessionParticipant


# every user has a profile; code that changes user.profile and then saves the
# user relies on the profile being saved along with it
@receiver(post_save, sender=User)
def create_or_save_profile(sender, instance, created, raw=False, **kwargs):
    if raw:  # loaddata: the fixture brings its own profiles
        return
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


# a new (or corrected) member who did a trial training: their request is done.
# Saving the user saves the profile too (above), so name changes land here as well.
@receiver(post_save, sender=Profile)
def mark_trial_member(sender, instance, raw=False, **kwargs):
    if raw:
        return
    mark_member(instance.user.first_name, instance.user.last_name, instance.birthday)


# a deleted trial request: the training sessions keep the attendance (for the participant
# count), but not the copied name and notes, which nothing would link to anymore
@receiver(pre_delete, sender=Tester)
def anonymise_trial_attendance(sender, instance, **kwargs):
    TrainingSessionParticipant.objects.filter(tester=instance).update(name="Probetraining (gelöscht)", notes=None)
