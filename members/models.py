from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse  # to get absolut_urls
from datetime import datetime, timedelta
from multiselectfield import MultiSelectField
from PIL import Image as Img
import json


def calculate_age(birth_date):
    today = datetime.today()
    age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )
    return age


# thats the base-class for external people
class Human(models.Model):
    first_name = models.CharField("Vorname", max_length=200, blank=True, null=True)
    last_name = models.CharField("Nachname", max_length=200, blank=True, null=True)
    email = models.CharField("Emailadresse", max_length=200, blank=True, null=True)
    sex = models.CharField("Geschlecht", max_length=200, blank=True, null=True)
    birthday = models.DateTimeField("Geburtstag", null=True, blank=True)
    telephone = models.CharField("Telephone", max_length=20, null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def age(self):
        if self.birthday:
            return calculate_age(self.birthday)
        return None


class News(models.Model):
    title = models.CharField("Titel", max_length=200)
    capture = models.TextField("Kurzbeschreibung", blank=True, null=True)
    content = models.TextField("Beitrag", blank=True, null=True)
    content_rendered = models.TextField(blank=True, null=True)
    picture = models.ImageField(
        "Stockphoto", blank=True, null=True, upload_to="uploads/news/images"
    )

    def __str__(self):
        return f"Beitrag: {self.title}"

    def get_absolute_url(self):
        return reverse("news_detail", kwargs={"pk": self.pk})


# Create your models here.
class Spot(models.Model):
    title = models.CharField("Spotname", max_length=30)
    lat = models.CharField("Latitude", max_length=30, default="51.347127")
    long = models.CharField("Longitude", max_length=30, default="12.350504")

    def __str__(self):
        return f"Spot: {self.title}"


## Event related models
class Document(models.Model):
    name = models.CharField("Name", max_length=200)
    file = models.FileField(
        "File", upload_to=f"uploads/events/docs", null=True, blank=True
    )
    # foreign key relationships to where files can be saved
    member_participants = models.ForeignKey(
        "Participant", on_delete=models.CASCADE, null=True, blank=True
    )
    event_public = models.ForeignKey(
        "Event",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Zusätzliche Dateien",
        related_name="public_docs",
    )
    event_orga = models.ForeignKey(
        "Event",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Dokumente (Orga)",
        related_name="orga_docs",
    )

    def event_toggle(self):
        if self.event_public:
            self.event_orga = self.event_public
            self.event_public = None
        else:
            self.event_public = self.event_orga
            self.event_orga = None
        self.save()


class DescriptionImage(models.Model):
    image = models.ImageField("Foto", upload_to=f"uploads/descriptions/images/")


class Description(models.Model):
    content = models.TextField("content", blank=True, null=True)
    # to link the description to other models
    event = models.OneToOneField(
        "Event",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="description",
    )


# Participant extends human. make sure to skip all the steps that are then not required for members
class Participant(Human):
    # of which event?
    event = models.ForeignKey(
        "Event", on_delete=models.CASCADE, related_name="participant"
    )
    # who is it?
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # related to finances
    payed = models.BooleanField("Bezahlt", default=False)
    storno = models.BooleanField("Storno", default=False)
    # now the additional fields
    notes = models.TextField("Notizen", blank=True, null=True)
    answers = models.TextField("Formfelder", blank=True, null=True)

    @property
    def get_first_name(self):
        return self.user.first_name if self.user else self.first_name

    @property
    def get_last_name(self):
        return self.user.last_name if self.user else self.last_name

    @property
    def get_email(self):
        return self.user.email if self.user else self.email

    @property
    def get_sex(self):
        return self.user.profile.sex if self.user else self.sex

    @property
    def get_birthday(self):
        return self.user.profile.birthday if self.user else self.birthday

    @property
    def get_telephone(self):
        return self.user.profile.telephone if self.user else self.telephone

    @property
    def get_costs(self):
        if self.user:
            return self.event.costs
        return self.event.external_costs

    def __str__(self):
        return f"{self.get_first_name} {self.get_last_name}"

    def get_absolute_url(self):
        return self.event.get_absolute_url()

    @property
    def answer_dict(self):
        return json.loads(self.answers) if self.answers else {}

    def to_json(self):
        questions = {k: quest for k, (quest, type) in self.event.question_dict}
        answers = self.answer_dict
        tmp = {
            "id": self.pk,
            "Vorname": self.get_first_name,
            "Nachname": self.get_last_name,
            "Email": self.get_email,
            "Geschlecht": self.get_sex,
            "Geburtstag": self.get_birthday.strftime("%d.%m.%Y"),
            "Alter": calculate_age(self.get_birthday),
            "Telefonnummer": self.get_telephone,
            "Bezahlt": self.payed,
            "Notizen": self.notes,
        }
        tmp.update(
            {
                question: answers[q_key] if q_key in answers else "-"
                for q_key, question in questions.items()
            }
        )
        return tmp


class Event(models.Model):
    # very basic information
    info_only = models.BooleanField("Nur Ankündigung?", default=True)
    public_event = models.BooleanField("Öffentliche Veranstaltung", default=False)
    notes = models.CharField("Hinweis", blank=True, max_length=50)

    # for deletion
    deleted = models.BooleanField("Gelöscht", default=False)

    # what kind of event?
    title = models.CharField("Eventname", max_length=100)
    short = models.TextField("Kurzbeschreibung", blank=True, null=True)

    # time and place
    deadline = models.DateTimeField("Anmeldung/Abmeldung bis", blank=True, null=True)
    start_date = models.DateTimeField("Datum Beginn", blank=True, null=True)
    end_date = models.DateTimeField("Datum Ende", blank=True, null=True)
    place = models.CharField(
        "Veranstaltungsort", max_length=200, blank=True, default="Leipzig"
    )

    # what are the costs?
    costs = models.DecimalField(
        "Kosten für Mitglieder", blank=True, null=True, max_digits=8, decimal_places=2
    )
    external_costs = models.DecimalField(
        "Kosten für Nichtmitglieder",
        blank=True,
        null=True,
        max_digits=8,
        decimal_places=2,
    )

    # for participation?
    min_age = models.IntegerField("Mindestalter", default=0)
    max_age = models.IntegerField("Höchstalter", default=99)

    # questions for the participants
    questions = models.TextField("Formfelder", blank=True, null=True)

    # documents, maybe find a better way?
    teilnahmebedingungen = models.FileField(
        "Teilnahmebedingungen", upload_to=f"uploads/events/docs/", null=True, blank=True
    )
    datenschutz = models.FileField(
        "Datenschutzerklärung", upload_to=f"uploads/events/docs", null=True, blank=True
    )
    einverstaendnis = models.FileField(
        "Einverständniserklärung",
        upload_to=f"uploads/events/docs",
        null=True,
        blank=True,
    )

    # if we query over events, we want the most recent one firsthand
    class Meta:
        ordering = ["start_date"]

    # This we need to return the url on creating a new event
    def get_absolute_url(self):
        return reverse("get_event_detail", kwargs={"pk": self.pk})

    # this returns a list of pk of the users that are participants and are not marked
    # as cancelled
    @property
    def participant_users(self):
        return self.participant.filter(storno=False).values_list("user", flat=True)

    @property
    def hot_data(self):
        # return list of objects for the use in handsontables
        data = []
        for part in self.participant.all():
            data.append(part.to_json())
        return data

    @property
    def deadline_reached(self):
        return datetime.now().replace(tzinfo=None) > self.deadline.replace(
            tzinfo=None
        ) + timedelta(days=1)

    @property
    def multiple_days(self):
        return self.start_date.strftime("%d.%m") != self.end_date.strftime("%d.%m")

    @property
    def question_dict(self):
        return json.loads(self.questions).items() if self.questions else []

    def __str__(self):
        return f"Event: {self.title}{' (deleted)' if self.deleted else ''}"


class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    trainer_telnr = models.CharField(
        "Öffentliche Telefonnummer", max_length=100, blank=True, null=True
    )
    trainer_email = models.CharField(
        "Öffentliche Email", max_length=150, blank=True, null=True
    )
    image = models.ImageField("Profilbild", upload_to="uploads/trainer/profile_pics/")
    salary = models.CharField("Bezahlung", blank=True, null=True, max_length=5)
    license_level = models.CharField(
        "Lizenzstufe", max_length=100, blank=True, null=True
    )
    license_number = models.CharField(
        "Lizenznummer", max_length=100, blank=True, null=True
    )
    license_valid = models.DateTimeField("Gültigkeit", blank=True, null=True)
    license = models.FileField(
        "Lizenz", upload_to="uploads/trainer/docs", blank=True, null=True
    )
    contract = models.FileField(
        "Vertrag", upload_to="uploads/trainer/docs", blank=True, null=True
    )
    codex = models.FileField(
        "Ehrencodex", upload_to="uploads/trainer/docs", blank=True, null=True
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user.profile.member_num})"

    def get_absolute_url(self):
        return reverse("trainer_list")

    def save(self):
        super().save()
        img = Img.open(self.image.path)
        if img.height > img.width:
            cut = int((img.height - img.width) / 2)
            img = img.crop((0, 0 + cut, img.width, img.height - cut))
            img2 = img.resize((720, 720))
            img2.save(self.image.path)
        elif img.width > img.height:
            cut = int((img.width - img.height) / 2)
            img = img.crop((0 + cut, 0, img.width - cut, img.height))
            img2 = img.resize((720, 720))
            img2.save(self.image.path)

    def trainer_info(self):
        info = [f"Trainer:\t{self.user.first_name} {self.user.last_name}"]
        if self.license_number:
            info.append(f"Lizenznummer:\t{self.license_number}")
        if self.license_valid:
            info.append(f"Gültigkeit:\t{self.license_valid.strftime('%d.%m.%Y')}")

        return "\n".join(info)


class Session(models.Model):
    trainer = models.ManyToManyField(Trainer, blank=True, verbose_name="Trainer")
    spot = models.ForeignKey(
        Spot, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Spot"
    )

    title = models.CharField("Titel", max_length=50, default="Hallentraining")
    day = models.CharField("Tag", max_length=2, default="Mo")
    day_key = models.IntegerField("Key", default=1)

    start_time = models.TimeField("Beginn", default="17:00")
    end_time = models.TimeField("Ende", default="19:00")
    hinweis = models.CharField("Hinweis", blank=True, max_length=50)

    class Meta:
        ordering = ["start_time"]

    @property
    def trainerlist(self):
        return ",".join([x.user.first_name for x in self.trainer.all()])

    @property
    def format_start_time(self):
        return self.start_time.strftime("%H:%M")

    @property
    def format_end_time(self):
        return self.end_time.strftime("%H:%M")

    @property
    def order(self):
        tag = {
            "Mo": 1,
            "Di": 2,
            "Mi": 3,
            "Do": 4,
            "Fr": 5,
            "Sa": 6,
            "So": 7,
        }
        if self.day in tag:
            return tag[self.day]
        else:
            return 8

    @property
    def weekday(self):
        tag = {
            "Mo": "Montags",
            "Di": "Dienstags",
            "Mi": "Mittwochs",
            "Do": "Donnerstags",
            "Fr": "Freitags",
            "Sa": "Samstags",
            "So": "Sonntags",
        }
        if self.day in tag:
            return tag[self.day]
        else:
            return "Irgendwann"

    def get_absolute_url(self):
        return reverse("index")

    def __str__(self):
        return f"Session: {self.title}_{self.day}"

    class Meta:
        ordering = ["day_key"]


class Message(models.Model):
    choices = (("sessions", "Sessions"), ("events", "Events"))
    title = models.CharField("Titel", max_length=200)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    message = models.TextField(
        "Hinweis", default="Deine Nachricht hier", blank=True, null=True
    )
    date = models.DateTimeField(default=datetime(2020, 11, 14, 1, 54, 52, 799289))
    autodelete = models.DateTimeField("Automatisches Löschen", blank=True, null=True)
    display = models.CharField(max_length=20, choices=choices, blank=True)

    def save(self, *args, **kwargs):
        self.date = datetime.today()
        super().save(*args, **kwargs)

    @property
    def delme(self):
        if not self.autodelete:
            return False
        return datetime.now().replace(tzinfo=None) > self.autodelete.replace(
            tzinfo=None
        ) + timedelta(days=1)

    def __str__(self):
        return f"Message: {self.title}"

    def get_absolute_url(self):
        return reverse("index")


class Chairman(models.Model):
    choices = (
        ("member_site", "Anzeige Mitglieder"),
        ("interested_site", "Anzeige Interessierte"),
        ("event_site", "Anzeige Veranstalter"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    public_telnr = models.CharField(
        "Öffentliche Telefonnummer", max_length=100, blank=True, null=True
    )
    public_email = models.CharField(
        "Öffentliche Email", max_length=150, blank=True, null=True
    )
    competences = models.TextField("Zuständigkeiten (mit Komma getrennt)")
    image = models.ImageField("Profilbild", upload_to="uploads/chairmen/profile_pics/")
    show = MultiSelectField(choices=choices, blank=True, max_length=300)

    def __str__(self):
        return f"Vorstand: {self.user.first_name} {self.user.last_name}"

    @property
    def complist(self):
        return self.competences.split(",")

    def get_absolute_url(self):
        return reverse("chairman_list")

    def save(self):
        super().save()
        img = Img.open(self.image.path)
        if img.height > img.width:
            cut = int((img.height - img.width) / 2)
            img = img.crop((0, 0 + cut, img.width, img.height - cut))
            img2 = img.resize((720, 720))
            img2.save(self.image.path)
        elif img.width > img.height:
            cut = int((img.width - img.height) / 2)
            img = img.crop((0 + cut, 0, img.width - cut, img.height))
            img2 = img.resize((720, 720))
            img2.save(self.image.path)


class Profile(models.Model):
    choices = (
        ("Ordentliches Mitglied", "Ordentliches Mitglied"),
        ("Förderndes Mitglied", "Förderndes Mitglied"),
        ("Pausiertes Mitglied", "Pausiertes Mitglied"),
        ("Kündigung", "Kündigung"),
    )
    choices2 = (
        ("SEPA", "SEPA"),
        ("Dauerauftrag", "Dauerauftrag"),
        ("Überweisung", "Überweisung"),
    )

    # peronal data
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birthday = models.DateTimeField("Geburtstag", null=True, blank=True)
    address = models.CharField("Adresse", max_length=300, null=True, blank=True)
    telephone = models.CharField("Telephone", max_length=20, null=True, blank=True)
    sex = models.CharField("Geschlecht", max_length=1)

    # for u18
    parent = models.CharField(
        "Ansprechpartner*in", max_length=100, null=True, blank=True
    )
    parent_telnr = models.CharField(
        "Notfallnummer", max_length=100, null=True, blank=True
    )

    # club data
    status = models.CharField(
        max_length=40, choices=choices, default="Ordentliches Mitglied"
    )
    member_num = models.CharField("Mitgliedsnummer", blank=True, max_length=30)
    membership_start = models.DateTimeField(
        "Beginn der Mitgliedschaft", null=True, blank=True
    )
    membership_end = models.DateTimeField("Kündigung zum", null=True, blank=True)
    ermaessigt = models.BooleanField("Ermäßigt?", default=False)
    mandatsref = models.CharField(
        "Mandatsreferenz", max_length=40, null=True, blank=True
    )
    zahlungsart = models.CharField(
        "Zahlungsart", choices=choices2, max_length=30, default="SEPA"
    )
    beitrag = models.IntegerField("Beitragshöhe", default=20)
    notes_trainer = models.TextField(
        "Notizen für den/die Trainer*in", null=True, blank=True
    )
    notes_chairman = models.TextField("Notizen für den Vorstand", null=True, blank=True)
    # permission handling
    permission_level = models.IntegerField("Permission Level", default=0)

    class Meta:
        ordering = ["member_num"]

    @property
    def privileged(self):
        return (
            hasattr(self.user, "chairman")
            or self.user.is_superuser
            or hasattr(self.user, "trainer")
        )

    @property
    def age(self):
        if self.birthday:
            return calculate_age(self.birthday)
        return None

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_absolute_url(self):
        return reverse("member_list")


class AdditionalEmail(models.Model):
    title = models.CharField("Titel", max_length=200, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.CharField("Emailadresse", max_length=200, blank=True, null=True)
