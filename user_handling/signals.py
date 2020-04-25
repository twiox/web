"""from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from members.models import Profile

#sender = User, receiver = Profile
#this basially means - create profile if user is created
#dont frorget the ready() method in apps.py

@receiver(post_save, sender=User) 
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance,member_num=kwargs["mitgl_nr"])

#when User is created (sender), the post_save fires.
#the receiver runs the function and the instance of the created user
#is saved for the profile

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()
"""