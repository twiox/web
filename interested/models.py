from django.db import models
from PIL import Image
from django.urls import reverse
from datetime import datetime, timedelta
from members.models import User
from django.template.defaultfilters import slugify
import markdown

# Create your models here.
class ContactPerson(models.Model):
    tag = models.CharField('Nach diesem Schlagwort wird gefiltert (z.B. Twiju)', max_length=300)
    picture = models.ImageField("Foto", upload_to="contacts/")
    name = models.CharField("Name", max_length=100, default="Jon Doe")
    public_telnr = models.CharField("Telefonnummer", max_length=100, blank=True, null=True)
    public_email = models.CharField("Email", max_length=150, blank=True, null=True)

    def save(self):
        super().save()
        img = Image.open(self.picture.path)
        if(img.height > img.width):
            cut = int((img.height-img.width)/2)
            img = img.crop((0, 0+cut, img.width, img.height-cut))
            img2 = img.resize((720,720))
            img2.save(self.picture.path)
        elif(img.width > img.height):
            cut = int((img.width-img.height)/2)
            img = img.crop((0+cut, 0, img.width-cut, img.height))
            img2 = img.resize((720,720))
            img2.save(self.picture.path)


class Teamer(models.Model):
    choices =(
        ("leipzig","Leipzig"),
        ("jena","Jena")
    )
    priority = models.IntegerField()
    city = models.CharField("Stadt",max_length=30,choices=choices,blank=True)

    picture = models.ImageField("Foto", upload_to="team_pictures/")
    name = models.CharField("Name", max_length=100, default="Jon Doe")
    position = models.CharField("Position", max_length=100, default="Trainer")
    notes = models.TextField("Sonstiges", blank=True)
    public_telnr = models.CharField("Telefonnummer", max_length=100, blank=True, null=True)
    public_email = models.CharField("Email", max_length=150, blank=True, null=True)

    def get_absolute_url(self):
        return reverse('team')

    def save(self):
        super().save()
        img = Image.open(self.picture.path)
        if(img.height > img.width):
            cut = int((img.height-img.width)/2)
            img = img.crop((0, 0+cut, img.width, img.height-cut))
            img2 = img.resize((720,720))
            img2.save(self.picture.path)
        elif(img.width > img.height):
            cut = int((img.width-img.height)/2)
            img = img.crop((0+cut, 0, img.width-cut, img.height))
            img2 = img.resize((720,720))
            img2.save(self.picture.path)

    class Meta:
        ordering = ["priority"]


class PublicEvent(models.Model):

    title = models.CharField("Event-name", max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True)
    header_picture = models.ImageField("Veranstaltungsbild", upload_to="PublicEvents/Images/Headers")
    thumbnail_long = models.ImageField("Thumbnail Landscape format", upload_to="PublicEvents/Images/Headers",blank=True, null=True)
    thumbnail_high = models.ImageField("Thumbnail Portrait format", upload_to="PublicEvents/Images/Headers",blank=True, null=True)
    place = models.CharField("Veranstaltungsort", max_length=200, blank=True, default="Leipzig")
    capture =  models.TextField("Kurzbeschreibung", blank=True, null=True)
    description = models.TextField("Beschreibung", blank=True)
    description_rendered = models.TextField(blank=True, null=True)
    deadline = models.DateTimeField("Anmeldung/Abmeldung bis", default= datetime(2020, 11, 14, 1, 54, 52, 799289))
    start_date = models.DateTimeField("Datum Beginn", default= datetime(2020, 11, 14, 1, 54, 52, 799289))
    end_date = models.DateTimeField("Datum Ende", default= datetime(2020, 11, 14, 1, 54, 52, 799289))
    hinweis = models.CharField("Hinweis", blank=True, max_length=50)
    base_costs = models.FloatField("Kosten", blank=True, null=True)
    info_only = models.BooleanField("Nur Ankündigung?",default=False)

    teilnahmebedingungen = models.FileField("Teilnahmebedingungen", upload_to=f"PublicEvents/Docs/",null=True,blank=True)
    datenschutz = models.FileField("Datenschutzerklärung",upload_to=f"PublicEvents/Docs/",null=True,blank=True)
    einverstaendnis = models.FileField("Einverständnis",upload_to=f"PublicEvents/Docs/",null=True,blank=True)

    #if we query over events, we want the most recent one firsthand
    class Meta:
        ordering = ["start_date"]

    def save(self, *args, **kwargs):
        self.slug = self.slug or slugify(self.title)
        self.description_rendered = markdown.markdown(self.description)
        super().save(*args, **kwargs)


    #This we need to return the url on creating a new event
    def get_absolute_url(self):
        return reverse('public_event', kwargs={"event_slug": self.slug})

    @property
    def is_past_due(self):
        return datetime.now().replace(tzinfo=None) > self.end_date.replace(tzinfo=None) + timedelta(days=3)
    @property
    def deadline_reached(self):
        return datetime.now().replace(tzinfo=None) > self.deadline.replace(tzinfo=None)

    def __str__(self):
        return f"PublicEvent: {self.title}"



class EventMerch(models.Model):
    event = models.ForeignKey(PublicEvent, on_delete=models.CASCADE, verbose_name = u"Event",blank=True, null=True)
    title = models.CharField("Titel", max_length=200)
    image = models.ImageField("Artikelbild", upload_to="PublicEvents/Images/Merch")
    price = models.CharField("Preis", max_length=10)
    sizes = models.TextField("Größen", default = "XS\tS\tM\tL\tXL\tXXL")
    description = models.TextField("Beschreibung", blank=True, null=True)
    description_rendered = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.description_rendered = markdown.markdown(self.description)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"EventMerch_{self.title}"


class EventParticipant(models.Model):
    event = models.ForeignKey(PublicEvent, on_delete=models.CASCADE, verbose_name = u"Event_ID", blank=True, null=True)
    first_name = models.CharField("Vorname", max_length=300)
    last_name = models.CharField("Nachname", max_length=300)
    birthday = models.DateTimeField("Geburtsdatum")
    email = models.CharField("Emailadresse", max_length=300)
    phone = models.CharField("Telefonnummer",max_length=30,blank=True,null=True)
    contact = models.CharField("Kontaktmöglichkeit", max_length=200, blank=True,null=True) #for the journey. Dropdown in UI
    invoice = models.FloatField("Kosten", blank=True, null=True)
    payed = models.BooleanField("Bezahlt", default=False)
    merch_wanted = models.BooleanField("Merch bestellt", default=False)
    merch_size = models.CharField("Größe", max_length=200, blank=True, null=True)
    notes = models.TextField("Notizen", blank=True, null=True)

    def __str__(self):
        return f"Participant_{self.first_name}_{self.last_name}"


class PublicEventParticipantMerch(models.Model):
    merch = models.ManyToManyField(EventMerch)
    participant = models.ManyToManyField(EventParticipant)
    size = models.CharField("Größe", max_length=100)



































