from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse #to get absolut_urls
from datetime import datetime
from multiselectfield import MultiSelectField


# Create your models here.

class Spot(models.Model):
    title = models.CharField("Spotname", max_length=30)
    lat = models.CharField("Latitude", max_length=30, default="51.347127")
    long = models.CharField("Longitude", max_length=30,default="12.350504")
    description = models.TextField("Beschreibung, Zusatzinformation", default="Lorem Ipsum")
    picture = models.ImageField("Foto vom Spot", default = "spot_placeholder.jpg", upload_to="spot_pics/")

    def __str__(self):
        return f"Spot: {self.title}"
        
    def get_absolute_url(self):
        return reverse('spot_detail', kwargs={"pk": self.pk})

class Group(models.Model):
    group_id = models.CharField("Gruppe (z.B 'A')", max_length=10)

    def __str__(self):
        return f"Gruppe: {self.group_id}"

    def get_absolute_url(self):
        return reverse('group_list')


class Event(models.Model):
    allowed_groups = models.ManyToManyField(Group, verbose_name="Für die Gruppen")
    participants = models.ManyToManyField(User, blank=True)
    
    title = models.CharField("Event-name", max_length=100)
    place = models.CharField("Veranstaltungsort", max_length=200, blank=True, default="Leipzig")
    description = models.TextField("Beschreibung", blank=True)
    deadline = models.DateTimeField("Anmeldung/Abmeldung bis", default=datetime.now())
    start_date = models.DateTimeField("Datum Beginn", default=datetime.now())
    end_date = models.DateTimeField("Datum Ende", default=datetime.now())
    hinweis = models.CharField("Hinweis", blank=True, max_length=50)

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
    image = models.ImageField("Profilbild", upload_to="profile_pics/")
    
    def __str__(self):
        return f"{self.user.first_name}"
    
    def get_absolute_url(self):
        return reverse('trainer_update')

class Session(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name = u"Gruppe",blank=True, null=True,)
    trainer = models.ManyToManyField(Trainer, blank=True, verbose_name =u"Trainer")
    spot = models.ForeignKey(Spot, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=u"Spot")
    
    title = models.CharField("Titel", max_length=50, default="Hallentraining")
    day = models.CharField("Tag",max_length=2, default="Mo")
    start_time = models.TimeField("Beginn",default="17:00")
    end_time = models.TimeField("Ende",default="19:00")
    hinweis = models.CharField("Hinweis", blank=True, max_length=50)
    
    @property
    def format_start_time(self):
        return self.start_time.strftime("%H:%M")
    
    @property
    def format_end_time(self):
        return self.end_time.strftime("%H:%M")
    
    @property
    def weekday(self):
        tag={
        "Mo":"Montags",
        "Di":"Dienstags",
        "Mi":"Mittwochs",
        "Do":"Donnerstags",
        "Fr":"Freitags",
        "Sa":"Samstags",
        "So":"Sonntags",
        }
        return tag[self.day]
    
    
    def get_absolute_url(self):
        return reverse('session_detail', kwargs={"pk": self.pk})
    
    class Meta:
        ordering = ["day"]

    def __str__(self):
        return f"{self.title}_{self.group.group_id_self.day}"

class Message(models.Model):
    choices =(
        ("sessions","Sessions"),
        ("events","Events")
    )
    title = models.CharField("Titel",max_length=30)
    author = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    message = models.TextField("Hinweis",default = "Deine Nachricht hier")
    date = models.DateTimeField(default=datetime.now())
    display = models.CharField(max_length=20, choices=choices, blank=True)
    groups = models.ManyToManyField(Group,verbose_name="Für die Gruppen")
    
    def __str__(self):
        return f"Message {self.title}"
    
    def get_absolute_url(self):
        return reverse('index')

class Chairman(models.Model):
    choices = (('member_site', 'Anzeige Mitglieder'),
              ('interested_site', 'Anzeige Interessierte'),
              ('event_site', 'Anzeige Veranstalter'))

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    public_telnr = models.CharField("Öffentliche Telefonnummer", max_length=100, default = "Hier die Nummer für die Website")
    public_email = models.CharField("Öffentliche Email", max_length=150, default = "Hier die Email für die Website")
    competences = models.TextField("Zuständigkeiten (mit Komma getrennt)")
    image = models.ImageField("Profilbild", upload_to="profile_pics/")
    show = MultiSelectField(choices=choices, blank=True)
    
    def __str__(self):
        return f"Vorstand: {self.user.username}"
    @property
    def complist(self):
        return self.competences.split(",")
    
    def get_absolute_url(self):
        return reverse('index')

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    member_num = models.CharField("Mitgliedsnummer", blank=True, max_length=30)
    group = models.ForeignKey(Group, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.user.username}\'s Profile"













