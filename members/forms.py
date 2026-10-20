from django import forms
from user_handling.forms import MdcFormMixin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Event, Session, Spot, Document, Trainer


class EventFileForm(forms.ModelForm):
    orga = forms.BooleanField(required=False)

    class Meta:
        model = Document
        fields = ["name", "file", "orga"]


class SpotForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SpotForm, self).__init__(*args, **kwargs)
        self.fields["description"].strip = False

    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Spot
        fields = ["title", "lat", "long", "description"]


WEEKDAYS = [("Mo", "Montag"), ("Di", "Dienstag"), ("Mi", "Mittwoch"), ("Do", "Donnerstag"),
            ("Fr", "Freitag"), ("Sa", "Samstag"), ("So", "Sonntag")]


class SessionForm(MdcFormMixin, forms.ModelForm):
    day = forms.ChoiceField(label="Tag", choices=WEEKDAYS)

    class Meta:
        model = Session
        fields = ["title", "day", "start_time", "end_time", "spot", "hinweis", "min_age", "max_age", "trainer"]
        labels = {"title": "Titel", "spot": "Ort", "hinweis": "Hinweis (z.B. fällt aus)", "trainer": "Trainer*innen"}
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


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "place",
            "info_only",
            "ask_ticket",
            "costs",
            "start_date",
            "end_date",
            "deadline",
            "hinweis",
            "description",
            "min_age",
            "max_age",
            "teilnahmebedingungen",
            "datenschutz",
            "einverstaendnis",
        ]



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
