from decimal import Decimal, InvalidOperation

from django import forms
from user_handling.forms import MdcFormMixin, date_widget
from django.contrib.auth.models import User
from .event_content import clean_content
from .models import Event, EventAsset, Message, Session, Spot, Document, Trainer


class EventFileForm(forms.ModelForm):
    orga = forms.BooleanField(required=False)

    class Meta:
        model = Document
        fields = ["name", "file", "orga"]


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
    autodelete = forms.DateField(label="Automatisch löschen nach", required=False, widget=date_widget())

    class Meta:
        model = Message
        fields = ["title", "message", "autodelete", "sessions"]
        labels = {"title": "Titel", "message": "Text", "sessions": "Für welche Trainingszeiten?"}
        widgets = {"message": forms.Textarea, "sessions": forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].widget.attrs["rows"] = 4
        sessions = self.fields["sessions"]
        sessions.queryset = Session.objects.order_by("day_key", "start_time")
        sessions.widget.attrs.pop("class", None)  # rendered as chips, not as a text field
        sessions.label_from_instance = lambda s: f"{s.title}, {s.day} {s.format_start_time}" + (f" ({s.age_label})" if s.age_label else "")


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
            "teilnahmebedingungen", "datenschutz", "einverstaendnis",
        ]
        labels = {
            "title": "Titel",
            "costs": "Kosten (€)",
            "hinweis": "Warnhinweis",
            "info_only": "Nur Ankündigung",
            "ask_ticket": "Deutschlandticket abfragen",
            "einverstaendnis": "Einverständniserklärung",
            "meeting_point": "Beschreibung (z.B. Haupteingang)",
        }
        widgets = {
            "teilnahmebedingungen": forms.FileInput,
            "datenschutz": forms.FileInput,
            "einverstaendnis": forms.FileInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["costs"].required = True
        for name in ["info_only", "ask_ticket", "content", *self.file_field_names]:
            self.fields[name].widget.attrs.pop("class", None)  # not rendered as text fields
        for name in self.file_field_names:
            self.fields[name].widget.attrs["hidden"] = True  # opened by the "Datei wählen" button
        if self.instance.has_legacy_description:
            del self.fields["content"]  # the old Markdown text stays as it is
        self.used_assets = []

    file_field_names = ["teilnahmebedingungen", "datenschutz", "einverstaendnis"]

    @property
    def file_fields(self):
        return [self[name] for name in self.file_field_names]

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


class UpdateMemberInformationForm(forms.ModelForm):
    comment = forms.CharField(label="Kommentar", widget=forms.Textarea, required=False)
    attachment = forms.FileField(label="Anhänge", required=False)

    class Meta:
        model = User
        fields = ["comment", "attachment"]


class UpdateMemberEmailForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    email1 = forms.EmailField()
    email2 = forms.EmailField()

    class Meta:
        model = User
        fields = ["password", "email1", "email2"]
