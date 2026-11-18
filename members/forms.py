from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django import forms
from django.db.models import Q
from user_handling.forms import MdcFormMixin, date_widget
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from .event_content import clean_content
from .models import Event, EventAsset, Message, Profile, Session, Spot, Document, Trainer


class EventFileForm(MdcFormMixin, forms.ModelForm):
    """Document upload on the orga page; "orga" keeps it from the event page."""

    orga = forms.BooleanField(label="Nur für die Orga", required=False)

    class Meta:
        model = Document
        fields = ["name", "file", "orga", "requires_consent"]
        widgets = {"file": forms.FileInput}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].required = True
        for name in ["file", "orga", "requires_consent"]:
            self.fields[name].widget.attrs.pop("class", None)  # not rendered as text fields
        self.fields["file"].widget.attrs["hidden"] = True  # opened by the "Datei wählen" button


class CoordinateField(forms.DecimalField):
    """Latitude (limit 90) or longitude (limit 180), rounded to the 6 decimal places the models store.

    Coordinates copied from other maps often have more decimals; 6 are about 10 cm.
    """

    def __init__(self, limit, **kwargs):
        super().__init__(
            min_value=-limit, max_value=limit, max_digits=9, decimal_places=6,
            widget=forms.NumberInput(attrs={"step": "any"}), **kwargs,
        )

    def to_python(self, value):
        value = super().to_python(value)
        if value is None:
            return None
        try:
            return value.quantize(Decimal("0.000001"))
        except InvalidOperation:  # far too large to round; the range check would reject it anyway
            raise forms.ValidationError(self.error_messages["invalid"], code="invalid")


class SpotForm(MdcFormMixin, forms.ModelForm):
    lat = CoordinateField(90, label="Breitengrad")
    long = CoordinateField(180, label="Längengrad")

    class Meta:
        model = Spot
        fields = ["title", "description", "lat", "long"]
        labels = {"description": "Kurze Beschreibung (z.B. Eingang, Treffpunkt)"}
        widgets = {
            "description": forms.Textarea,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].widget.attrs["rows"] = 3


class MessageForm(MdcFormMixin, forms.ModelForm):
    """Notice for the training times (kind "sessions") or for the event calendar (kind "events")."""

    autodelete = forms.DateField(label="Automatisch löschen nach", required=False, widget=date_widget())

    class Meta:
        model = Message
        fields = ["title", "message", "autodelete", "sessions", "events"]
        labels = {
            "title": "Titel",
            "message": "Text",
            "sessions": "Für welche Trainingszeiten?",
            "events": "Für welche Veranstaltungen?",
        }
        help_texts = {
            "sessions": "Sichtbar für alle, die eine der gewählten Trainingszeiten sehen. Keine Auswahl: für alle Mitglieder.",
            "events": "Sichtbar für alle, die eine der gewählten Veranstaltungen sehen. Keine Auswahl: für alle Mitglieder.",
        }
        widgets = {
            "message": forms.Textarea,
            "sessions": forms.CheckboxSelectMultiple,
            "events": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, kind="sessions", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].widget.attrs["rows"] = 4
        # only the choices that fit the kind of notice
        del self.fields["events" if kind == "sessions" else "sessions"]
        self.choice_name = kind
        choices = self.fields[kind]
        choices.widget.attrs.pop("class", None)  # rendered as chips, not as a text field
        if kind == "sessions":
            choices.queryset = Session.objects.order_by("day_key", "start_time")
            choices.label_from_instance = lambda s: f"{s.title}, {s.day} {s.format_start_time}" + (f" ({s.age_label})" if s.age_label else "")
        else:
            # events that are not over yet, plus the ones this notice is already linked to
            linked = self.instance.events.all() if self.instance.pk else Event.objects.none()
            choices.queryset = Event.objects.filter(
                Q(end_date__gte=datetime.now() - timedelta(days=3)) | Q(pk__in=linked)
            ).distinct().order_by("start_date")
            choices.label_from_instance = lambda e: f"{e.title}, {e.start_date:%d.%m.%Y}"

    @property
    def choice_field(self):
        return self[self.choice_name]


WEEKDAYS = [("Mo", "Montag"), ("Di", "Dienstag"), ("Mi", "Mittwoch"), ("Do", "Donnerstag"),
            ("Fr", "Freitag"), ("Sa", "Samstag"), ("So", "Sonntag")]


class SessionForm(MdcFormMixin, forms.ModelForm):
    day = forms.ChoiceField(label="Tag", choices=WEEKDAYS)

    class Meta:
        model = Session
        fields = ["title", "day", "start_time", "end_time", "spot", "hinweis", "min_age", "max_age", "trainer"]
        labels = {"title": "Titel", "spot": "Ort", "hinweis": "Hinweis (z.B. Mädchentraining)", "trainer": "Trainer*innen"}
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "end_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "trainer": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["trainer"].queryset = Trainer.objects.filter(active=True).select_related("user").order_by("user__last_name")
        self.fields["trainer"].widget.attrs.pop("class", None)  # rendered as chips, not as a text field
        self.fields["trainer"].label_from_instance = lambda t: f"{t.user.first_name} {t.user.last_name}"
        self.fields["spot"].label_from_instance = lambda spot: spot.title

    def save(self, commit=True):
        # day_key sorts the weekly overview
        self.instance.day_key = [key for key, _ in WEEKDAYS].index(self.cleaned_data["day"]) + 1
        return super().save(commit)


class EventForm(MdcFormMixin, forms.ModelForm):
    start_date = forms.DateTimeField(label="Beginn", widget=date_widget())
    end_date = forms.DateTimeField(label="Ende", widget=date_widget())
    deadline = forms.DateTimeField(label="Anmeldung/Abmeldung bis", widget=date_widget())
    # filled with the Editor.js output when the form is sent
    content = forms.JSONField(required=False, widget=forms.HiddenInput)
    meeting_lat = CoordinateField(90, label="Breitengrad", required=False)
    meeting_long = CoordinateField(180, label="Längengrad", required=False)

    class Meta:
        model = Event
        fields = [
            "title", "place", "costs", "start_date", "end_date", "deadline", "hinweis",
            "info_only", "ask_ticket", "min_age", "max_age", "content",
            "meeting_point", "meeting_lat", "meeting_long",
        ]
        labels = {
            "title": "Titel",
            "costs": "Kosten (€)",
            "hinweis": "Warnhinweis",
            "info_only": "Nur Ankündigung",
            "ask_ticket": "Deutschlandticket abfragen",
            "meeting_point": "Beschreibung (z.B. Haupteingang)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["costs"].required = True
        for name in ["info_only", "ask_ticket", "content"]:
            self.fields[name].widget.attrs.pop("class", None)  # not rendered as text fields
        if self.instance.has_legacy_description:
            del self.fields["content"]  # the old Markdown text stays as it is
        self.used_assets = []

    def clean_content(self):
        # uploads not yet linked to an event, plus the ones of this event
        assets = EventAsset.objects.filter(event=None)
        if self.instance.pk:
            assets = assets | self.instance.assets.all()
        content, self.used_assets = clean_content(
            self.cleaned_data["content"] or {"blocks": []},
            {asset.file.url: asset for asset in assets},
        )
        return content

    def clean(self):
        cleaned_data = super().clean()
        start, end = cleaned_data.get("start_date"), cleaned_data.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "Das Ende liegt vor dem Beginn.")
        lat, long = cleaned_data.get("meeting_lat"), cleaned_data.get("meeting_long")
        if (lat is None) != (long is None) and not self.has_error("meeting_lat") and not self.has_error("meeting_long"):
            self.add_error(None, "Für den Treffpunkt werden Breiten- und Längengrad gebraucht – oder keins von beiden.")
        return cleaned_data

    def save(self, commit=True):
        event = super().save(commit)
        if commit and "content" in self.fields:
            used = [asset.pk for asset in self.used_assets]
            EventAsset.objects.filter(pk__in=used).update(event=event)
            for asset in event.assets.exclude(pk__in=used):  # removed from the description
                asset.delete()
        return event


class EventUpdateParticipantForm(forms.ModelForm):
    confirm = forms.BooleanField()
    ticket = forms.BooleanField(required=False)

    class Meta:
        model = Event
        fields = ["confirm", "ticket"]


class EventUpdateParticipantForm2(forms.ModelForm):
    class Meta:
        model = Event
        fields = []


class ProfileSelfForm(MdcFormMixin, forms.ModelForm):
    """The data a member keeps up to date on their own profile page."""

    birthday = forms.DateField(label="Geburtsdatum", required=False, widget=date_widget())

    class Meta:
        model = Profile
        fields = ["birthday", "address", "telephone", "parent", "parent_telnr"]
        labels = {
            "address": "Adresse",
            "telephone": "Telefonnummer",
            "parent": "Ansprechpartner*in",
            "parent_telnr": "Notfallnummer",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # optional on the model, but every member needs them
        self.fields["address"].required = True
        self.fields["telephone"].required = True
        self.fields["birthday"].widget.attrs["max"] = datetime.now().strftime("%Y-%m-%d")

    def clean_birthday(self):
        birthday = self.cleaned_data.get("birthday")
        if birthday and birthday > datetime.now().date():
            raise forms.ValidationError("Das Geburtsdatum liegt in der Zukunft.")
        return birthday


class UpdateMemberInformationForm(forms.ModelForm):
    """Message from a member to the board, optionally with one attachment (e.g. a new SEPA mandate)."""

    MAX_ATTACHMENT = 5 * 1024 * 1024  # the page says 5 MB

    comment = forms.CharField(label="Nachricht", widget=forms.Textarea, error_messages={"required": "Bitte schreib eine Nachricht."})
    attachment = forms.FileField(label="Anhang", required=False)

    class Meta:
        model = User
        fields = ["comment", "attachment"]

    def clean_attachment(self):
        attachment = self.cleaned_data.get("attachment")
        if attachment and attachment.size > self.MAX_ATTACHMENT:
            raise forms.ValidationError("Der Anhang ist zu groß (höchstens 5 MB).")
        return attachment


class UpdateMemberEmailForm(MdcFormMixin, forms.Form):
    """New login and contact address; the password confirms it's really the member."""

    password = forms.CharField(label="Dein Passwort", widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))
    email1 = forms.EmailField(label="Neue E-Mail-Adresse", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    email2 = forms.EmailField(label="Neue E-Mail-Adresse wiederholen", widget=forms.EmailInput(attrs={"autocomplete": "email"}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("Das Passwort stimmt nicht.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("email1") and cleaned_data.get("email2") and cleaned_data["email1"] != cleaned_data["email2"]:
            self.add_error("email2", "Die E-Mail-Adressen stimmen nicht überein.")
        return cleaned_data


class UsernameForm(MdcFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["username"]
        labels = {"username": "Nutzername"}


class MemberPasswordChangeForm(MdcFormMixin, PasswordChangeForm):
    """Django's password change form in the site's field style."""
