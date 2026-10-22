from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.contrib.auth.models import User
from django.urls import reverse  # to get absolut_urls
from datetime import datetime, timedelta
from multiselectfield import MultiSelectField
from PIL import Image as Img, ImageOps
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from .event_content import render_content

PROFILE_PLACEHOLDER = "media/profile_placeholder.svg"


def crop_to_square(path):
    """Crops an image to a centered square of 720x720 px."""
    img = Img.open(path)
    if img.height == img.width:
        return
    cut = abs(img.height - img.width) // 2
    if img.height > img.width:
        img = img.crop((0, cut, img.width, img.height - cut))
    else:
        img = img.crop((cut, 0, img.width - cut, img.height))
    img.resize((720, 720)).save(path)


class News(models.Model):
    title = models.CharField("Titel", max_length=200)
    capture = models.TextField("Kurzbeschreibung", blank=True, null=True)
    content = models.TextField("Beitrag", blank=True, null=True)
    content_rendered = models.TextField(blank=True, null=True)
    picture = models.ImageField(
        "Stockphoto", blank=True, null=True, upload_to="beiträge/"
    )

    def __str__(self):
        return f"Beitrag: {self.title}"

    def get_absolute_url(self):
        return reverse("news_detail", kwargs={"pk": self.pk})


# Create your models here.
class Spot(models.Model):
    title = models.CharField("Spotname", max_length=30)
    lat = models.DecimalField("Breitengrad", max_digits=9, decimal_places=6, default=Decimal("51.347127"))
    long = models.DecimalField("Längengrad", max_digits=9, decimal_places=6, default=Decimal("12.350504"))
    description = models.TextField("Beschreibung", blank=True, default="")

    def __str__(self):
        return f"Spot: {self.title}"


class AgeRange(models.Model):
    """Optional age limits; an empty field means no limit on that side."""

    min_age = models.PositiveSmallIntegerField("Mindestalter", blank=True, null=True)
    max_age = models.PositiveSmallIntegerField("Höchstalter", blank=True, null=True)

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if self.min_age is not None and self.max_age is not None and self.min_age > self.max_age:
            raise ValidationError({"max_age": "Das Höchstalter muss mindestens so hoch sein wie das Mindestalter."})

    def allows_age(self, age):
        # members without a birthday see nothing that is age-dependent
        if age is None:
            return False
        return (self.min_age is None or age >= self.min_age) and (
            self.max_age is None or age <= self.max_age
        )

    @classmethod
    def visible_for_age(cls, age):
        if age is None:
            return cls.objects.none()
        return cls.objects.filter(
            Q(min_age__isnull=True) | Q(min_age__lte=age),
            Q(max_age__isnull=True) | Q(max_age__gte=age),
        )

    @property
    def age_label(self):
        if self.min_age is not None and self.max_age is not None:
            return f"{self.min_age}–{self.max_age} J."
        if self.min_age is not None:
            return f"ab {self.min_age} J."
        if self.max_age is not None:
            return f"bis {self.max_age} J."
        return ""


## Event related models
class Document(models.Model):
    name = models.CharField("Name", max_length=200)
    file = models.FileField(
        "File", upload_to=f"Events/Docs/etc/", null=True, blank=True
    )
    # public documents members have to accept when they sign up (e.g. Datenschutz, Einverständnis)
    requires_consent = models.BooleanField("Muss bei der Anmeldung bestätigt werden", default=False)
    # foreign key relationships to where files can be saved
    member_participants = models.ForeignKey(
        "MemberParticipant", on_delete=models.CASCADE, null=True, blank=True
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


class MemberParticipant(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )  # set null, so that we still see the number of participants even after user is gone
    payed = models.BooleanField("Bezahlt", default=False)
    notes = models.TextField("Notizen", blank=True, null=True)
    event = models.ForeignKey("Event", on_delete=models.CASCADE)
    storno = models.BooleanField("Storno", default=False)
    has_ticket = models.BooleanField("Deutschlandticket", default=False)
    # trainers/chairmen in charge of the event; participants see them as contact
    responsible = models.BooleanField("Verantwortlich", default=False)
    # ticked by the orga on site
    checked_in = models.BooleanField("Eingecheckt", default=False)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def contact(self):
        """Public photo and contact details: the trainer ones first, else the chairman ones."""
        trainer, chairman = getattr(self.user, "trainer", None), getattr(self.user, "chairman", None)
        return {
            "name": f"{self.user.first_name} {self.user.last_name}",
            "image": (trainer or chairman).image_url if (trainer or chairman) else static(PROFILE_PLACEHOLDER),
            "phone": (trainer and trainer.trainer_telnr) or (chairman and chairman.public_telnr) or "",
            "email": (trainer and trainer.trainer_email) or (chairman and chairman.public_email) or "",
        }


class Event(AgeRange):
    title = models.CharField("Event-name", max_length=100)
    place = models.CharField(
        "Veranstaltungsort", max_length=200, blank=True, default="Leipzig"
    )
    # Markdown from before the editor; still shown, but no longer editable
    description = models.TextField("Beschreibung", blank=True)
    description_rendered = models.TextField(blank=True, null=True)
    # Editor.js blocks, see event_content.py
    content = models.JSONField("Beschreibung", blank=True, null=True)
    deadline = models.DateTimeField("Anmeldung/Abmeldung bis", blank=True, null=True)
    start_date = models.DateTimeField("Datum Beginn", blank=True, null=True)
    end_date = models.DateTimeField("Datum Ende", blank=True, null=True)
    hinweis = models.CharField("Hinweis", blank=True, max_length=50)
    # optional meeting point, picked on a map; meant for the participants
    meeting_point = models.CharField("Treffpunkt", blank=True, max_length=100)
    meeting_lat = models.DecimalField("Breitengrad", max_digits=9, decimal_places=6, null=True, blank=True)
    meeting_long = models.DecimalField("Längengrad", max_digits=9, decimal_places=6, null=True, blank=True)
    costs = models.DecimalField(
        "Kosten", blank=True, null=True, max_digits=8, decimal_places=2
    )
    info_only = models.BooleanField("Nur Ankündigung?", default=False)
    ask_ticket = models.BooleanField("Deutschlandticket Abfragen", default=False)

    participants = models.ManyToManyField(User)

    # if we query over events, we want the most recent one firsthand
    class Meta:
        ordering = ["start_date"]

    # This we need to return the url on creating a new event
    def get_absolute_url(self):
        return reverse("event_detail", kwargs={"pk": self.pk})

    @property
    def participant_users(self):
        q = MemberParticipant.objects.filter(Q(event=self) & Q(storno=False))
        return list([part.user for part in q])

    @property
    def is_past_due(self):
        if self.end_date is None:  # some old events have none
            return False
        return datetime.now().replace(tzinfo=None) > self.end_date.replace(
            tzinfo=None
        ) + timedelta(days=3)

    @property
    def deadline_reached(self):
        if self.deadline is None:  # some old events have none
            return False
        return datetime.now().replace(tzinfo=None) > self.deadline.replace(
            tzinfo=None
        ) + timedelta(days=1)

    @property
    def multiple_days(self):
        if not self.start_date == self.end_date:
            return True
        return False

    @property
    def has_meeting_point(self):
        return bool(self.meeting_point) or self.has_meeting_coordinates

    @property
    def has_meeting_coordinates(self):
        return self.meeting_lat is not None and self.meeting_long is not None

    @property
    def has_legacy_description(self):
        return self.content is None and bool(self.description.strip())

    @property
    def description_html(self):
        if self.has_legacy_description:
            return mark_safe(self.description_rendered or "")
        return render_content(self.content)

    def __str__(self):
        return f"Event: {self.title}"


def event_asset_path(instance, filename):
    # media files are public, so the names must not be guessable
    return f"Events/Inhalte/{uuid4().hex}{Path(filename).suffix.lower()}"


class EventAsset(models.Model):
    """Image or file uploaded in the event editor; linked to its event once the event is saved."""

    IMAGE, FILE = "image", "file"
    kind = models.CharField(max_length=5, choices=[(IMAGE, "Bild"), (FILE, "Datei")])
    file = models.FileField(upload_to=event_asset_path)
    name = models.CharField(max_length=200)  # original file name, shown on download links
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, null=True, blank=True, related_name="assets"
    )
    uploaded = models.DateTimeField(auto_now_add=True)

    def shrink_image(self):
        """Scales big photos down; saving again also drops EXIF data like the GPS position."""
        with Img.open(self.file.path) as img:
            if img.format == "GIF":  # keep animations
                return
            img = ImageOps.exif_transpose(img)
            if Path(self.file.path).suffix in (".jpg", ".jpeg") and img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            img.thumbnail((1600, 1600))
            img.save(self.file.path, quality=85)


class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    trainer_telnr = models.CharField(
        "Öffentliche Telefonnummer", max_length=100, blank=True, null=True
    )
    trainer_email = models.CharField(
        "Öffentliche Email", max_length=150, blank=True, null=True
    )
    image = models.ImageField("Profilbild", upload_to="profile_pics/", blank=True)
    # switched off instead of deleted, so sessions, invoices and documents keep their trainer
    active = models.BooleanField("Aktiv", default=True)
    salary = models.DecimalField("TAE pro Stunde", max_digits=5, decimal_places=2, blank=True, null=True)
    license_level = models.CharField(
        "Lizenzstufe", max_length=100, blank=True, null=True
    )
    license_number = models.CharField(
        "Lizenznummer", max_length=100, blank=True, null=True
    )
    license_valid = models.DateTimeField("Gültigkeit", blank=True, null=True)
    license = models.FileField(
        "Lizenz", upload_to="trainer_stuff", blank=True, null=True
    )
    contract = models.FileField(
        "Vertrag", upload_to="trainer_stuff", blank=True, null=True
    )
    codex = models.FileField(
        "Ehrencodex", upload_to="trainer_stuff", blank=True, null=True
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user.profile.member_num})"

    def get_absolute_url(self):
        return reverse("trainer_list")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            crop_to_square(self.image.path)

    @property
    def image_url(self):
        return self.image.url if self.image else static(PROFILE_PLACEHOLDER)

    def trainer_info(self):
        info = [f"Trainer:\t{self.user.first_name} {self.user.last_name}"]
        if self.license_number:
            info.append(f"Lizenznummer:\t{self.license_number}")
        if self.license_valid:
            info.append(f"Gültigkeit:\t{self.license_valid.strftime('%d.%m.%Y')}")

        return "\n".join(info)


class Session(AgeRange):
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
    participants = models.ManyToManyField("Profile", related_name="session", blank=True)

    @property
    def billing_label(self):
        """Stored in the trainer billing tables, e.g. "Hallentraining (9–13 J.)"."""
        return f"{self.title} ({self.age_label})" if self.age_label else self.title

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
        return f"{self.title} ({self.day})"

    class Meta:
        ordering = ["day_key"]


class Message(models.Model):
    choices = (("sessions", "Sessions"), ("events", "Events"))
    title = models.CharField("Titel", max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    message = models.TextField(
        "Hinweis", default="Deine Nachricht hier", blank=True, null=True
    )
    date = models.DateTimeField(default=datetime(2020, 11, 14, 1, 54, 52, 799289))
    autodelete = models.DateTimeField("Automatisches Löschen", blank=True, null=True)
    display = models.CharField(max_length=20, choices=choices, blank=True)
    # whoever sees one of these sessions/events sees the message; none means everyone
    sessions = models.ManyToManyField(
        Session, verbose_name="Für die Trainingszeiten", related_name="messages", blank=True
    )
    events = models.ManyToManyField(
        Event, verbose_name="Für die Veranstaltungen", related_name="messages", blank=True
    )

    def save(self, *args, **kwargs):
        self.date = datetime.today()
        super().save(*args, **kwargs)

    @classmethod
    def visible_for_age(cls, age):
        if age is None:
            return cls.objects.none()
        sessions = Session.visible_for_age(age)
        events = Event.visible_for_age(age)
        return cls.objects.filter(
            Q(display="sessions", sessions__isnull=True)
            | Q(display="sessions", sessions__in=sessions)
            | Q(display="events", events__isnull=True)
            | Q(display="events", events__in=events)
        ).distinct()

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
        ("interested_xdream", "Anzeige XDream"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    public_telnr = models.CharField(
        "Öffentliche Telefonnummer", max_length=100, blank=True, null=True
    )
    public_email = models.CharField(
        "Öffentliche Email", max_length=150, blank=True, null=True
    )
    competences = models.TextField("Zuständigkeiten (mit Komma getrennt)", blank=True)
    image = models.ImageField("Profilbild", upload_to="profile_pics/", blank=True)
    # switched off instead of deleted, so the public profile is kept for later
    active = models.BooleanField("Aktiv", default=True)
    show = MultiSelectField(choices=choices, blank=True, max_length=300)

    def __str__(self):
        return f"Vorstand: {self.user.first_name} {self.user.last_name}"

    @property
    def complist(self):
        return [c.strip() for c in self.competences.split(",") if c.strip()]

    def get_absolute_url(self):
        return reverse("chairman_list")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            crop_to_square(self.image.path)

    @property
    def image_url(self):
        return self.image.url if self.image else static(PROFILE_PLACEHOLDER)


def calculate_age(birth_date):
    today = datetime.today()
    age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )
    return age


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

    class Meta:
        ordering = ["member_num"]

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


# For the several gallery-projects
class Gallery(models.Model):
    title = models.CharField("Title", max_length=200, blank=True)

    def __str__(self):
        return self.title


class Image(models.Model):
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE)
    image = models.ImageField("Image", upload_to=f"galleries/")
    title = models.CharField("Title", max_length=200, blank=True)
    alt = models.TextField("Alt text", null=True, blank=True)
    priority = models.IntegerField("Priority")

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

    def __str__(self):
        return self.title


class ShopItem(models.Model):
    title = models.CharField("Title", max_length=300, blank=True)
    description = models.TextField("Description", blank=True)
    description_rendered = models.TextField(blank=True, null=True)
    gallery = models.OneToOneField(Gallery, on_delete=models.CASCADE)
    price = models.DecimalField("Price", blank=True, max_digits=4, decimal_places=2)
    visible = models.BooleanField("Visible", default="True")
    priority = models.IntegerField("Priority", default=99)

    def __str__(self):
        return self.title

    @property
    def get_images(self):
        return Image.objects.filter(gallery=self.gallery).order_by("priority")

    @property
    def n_images_modulo(self):
        return len(Image.objects.filter(gallery=self.gallery)) % 3

    @property
    def n_images(self):
        return len(Image.objects.filter(gallery=self.gallery))
