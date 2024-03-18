from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Event, Session, Spot, Document


class EventForm(forms.ModelForm):
    start_date = forms.DateTimeField(
        label="Beginn der Veranstaltung",
        widget=forms.TextInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    end_date = forms.DateTimeField(
        label="Ende der Veranstaltung",
        widget=forms.TextInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    deadline = forms.DateTimeField(
        label="Anmeldungsdeadline",
        widget=forms.TextInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = Event
        fields = [
            "info_only",
            "trainer_only",
            "public_event",
            "notes",
            "title",
            "short",
            "start_date",
            "end_date",
            "deadline",
            "place",
            "costs",
            "external_costs",
            "min_age",
            "max_age",
            "teilnahmebedingungen",
            "einverstaendnis",
            "datenschutz",
        ]


#
#
# The old stuff
#
#


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


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = [
            "title",
            "day",
            "start_time",
            "end_time",
            "hinweis",
            "spot",
            "trainer",
        ]
        widgets = {
            "trainer": forms.CheckboxSelectMultiple,
        }


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
