from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime

# Create your models here.

class Spot(models.Model):
    title = models.CharField(max_length=30)
    coords = models.CharField(max_length=100)
    #adress = models.TextField(blank=True)

    def __str__(self):
        return f"Spot: {self.title}"


class Session(models.Model):
    title = models.CharField(max_length=50, default="Halle_GruppeA_Sa")
    website_title = models.CharField(max_length=50, default="Hallentraining")
    spot = models.ForeignKey(Spot, blank=True, null=True, on_delete=models.SET_NULL)
    day = models.CharField(max_length=2, default="Mo")
    start_time = models.TimeField(default=datetime.now())
    end_time = models.TimeField(default=datetime.now())
    hinweis = models.CharField(blank=True, max_length=50)

    def __str__(self):
        return f"Session: {self.title}"

class Event(models.Model):
    titel = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField(default=datetime.now())
    end_date = models.DateTimeField(default=datetime.now())
    hinweis = models.CharField(blank=True, max_length=50)

    #if we query over events, we want the most recent one firsthand 
    class Meta:
        ordering = ["start_date"]

    def __str__(self):
        return f"Event: {self.titel}"


class Group(models.Model):
    group_id = models.CharField(max_length=10)
    schedule = models.ManyToManyField(Session, blank=True)
    group_events = models.ManyToManyField(Event, blank=True)

    def __str__(self):
        return f"Gruppe: {self.group_id}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    stati = (("aktiv","Aktiv"),("fördernd","Fördernd"),("kündigung","Kündigung"),("pausiert","Pausiert"),)
    
    image = models.ImageField(default = "default.jpg", upload_to="profile_pics/")
    member_num = models.CharField(blank=True, max_length=30)
    status = models.CharField(max_length=30, choices=stati, default="aktiv")
    group = models.ForeignKey(Group, blank=True, null=True, on_delete=models.SET_NULL)
    email = models.EmailField(blank=True)
    telnr = models.CharField(blank=True, max_length=30)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}\'s Profile"

class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    groups = models.ManyToManyField(Group, blank=True)
    
    def __str__(self):
        return f"Trainer: user.username"








