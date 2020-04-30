from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse #to get absolut_urls
from datetime import datetime

# Create your models here.

class Spot(models.Model):
    title = models.CharField("Spotname", max_length=30)
    coords = models.CharField("Coordinaten", max_length=100)
    adress = models.TextField("Adresse/Wegbeschreibung", blank=True)
    picture = models.ImageField("Foto vom Spot", default = "spot_placeholder.jpg", upload_to="spot_pics/")

    def __str__(self):
        return f"Spot: {self.title}"
    
    def get_absolute_url(self):
        return reverse('spot_detail', kwargs={"pk": self.pk})

class Group(models.Model):
    group_id = models.CharField("Gruppe (z.B 'A')", max_length=10)

    def __str__(self):
        return f"Gruppe: {self.group_id}"


class Event(models.Model):
    allowed_groups = models.ManyToManyField(Group)
    participants = models.ManyToManyField(User, blank=True)
    
    title = models.CharField("Event-name", max_length=100)
    place = models.CharField("Veranstaltungsort", max_length=200, blank=True, default="Leipzig")
    description = models.TextField("Beschreibung", blank=True)
    deadline = models.DateTimeField("Anmeldung/Abmeldung bis", default=datetime.now())
    start_date = models.DateTimeField("Datum Beginn", default=datetime.now())
    end_date = models.DateTimeField("Datum Ende", default=datetime.now())
    hinweis = models.CharField("Hinweis (rote Anzeige)", blank=True, max_length=50)

    #if we query over events, we want the most recent one firsthand 
    class Meta:
        ordering = ["start_date"]
    
    #This we need to return the url on creating a new event 
    def get_absolute_url(self):
        return reverse('event_detail', kwargs={"pk": self.pk})
    
    @property
    def is_past_due(self):
        return datetime.now().replace(tzinfo=None) > self.start_date.replace(tzinfo=None)
    @property
    def deadline_reached(self):
        return datetime.now().replace(tzinfo=None) > self.deadline.replace(tzinfo=None)
    
    def __str__(self):
        return f"Event: {self.title}"


class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    trainer_telnr = models.CharField("Öffentliche Telefonnummer", max_length=100, default = "Hier die Nummer für die Website")
    trainer_email = models.CharField("Öffentliche Email", max_length=150, default = "Hier die Email für die Website")
    image = models.ImageField("Profilbild", default = "default.jpg", upload_to="profile_pics/")
    
    def __str__(self):
        return f"Trainer: {self.user.username}"

class Session(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    trainer = models.ManyToManyField(Trainer)
    spot = models.ForeignKey(Spot, blank=True, null=True, on_delete=models.SET_NULL)
    
    title = models.CharField("Titel für uns", max_length=50, default="Halle_GruppeA_Sa")
    website_title = models.CharField("Titel für Website", max_length=50, default="Hallentraining")
    day = models.CharField("Tag",max_length=2, default="Mo")
    start_time = models.TimeField("Beginn",default="17:00")
    end_time = models.TimeField("Ende",default="19:00")
    hinweis = models.CharField("Hinweise (rote Anzeige)", blank=True, max_length=50)
    
    @property
    def format_start_time(self):
        return self.start_time.strftime("%H:%M")
    
    @property
    def format_end_time(self):
        return self.end_time.strftime("%H:%M")
    
    def get_absolute_url(self):
        return reverse('session_detail', kwargs={"pk": self.pk})
    
    class Meta:
        ordering = ["day"]

    def __str__(self):
        return f"Session: {self.title}"

class Message(models.Model):
    choices = (("sessions","Sessions"),("events","Events"))
    title = models.CharField("Titel",max_length=30)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(default = "Deine Nachricht hier")
    expire_date = models.DateTimeField(default=datetime.now())
    display = models.CharField(max_length=20, choices=choices)
    
    def __str__(self):
        return f"Message {self.title}"

class Chairman(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    public_telnr = models.CharField("Öffentliche Telefonnummer", max_length=100, default = "Hier die Nummer für die Website")
    public_email = models.CharField("Öffentliche Email", max_length=150, default = "Hier die Email für die Website")
    competences = models.TextField("Zuständigkeiten (mit Komma getrennt)")
    image = models.ImageField("Profilbild", default = "default.jpg", upload_to="profile_pics/")
    
    def __str__(self):
        return f"Vorstand: {self.user.username}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    member_num = models.CharField("Mitgliedsnummer", blank=True, max_length=30)
    group = models.ForeignKey(Group, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.user.username}\'s Profile"













