from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Event, Spot, Document, Tester, Message, Session
from datetime import datetime


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
            "header",
            "info_only",
            "trainer_only",
            "public_event",
            "notes",
            "title",
            "short",
            "square",
            "start_date",
            "end_date",
            "deadline",
            "place",
            "costs",
            "external_costs",
            "external_spots",
            "min_age",
            "max_age",
            "teilnahmebedingungen",
            "einverstaendnis",
            "datenschutz",
        ]


class TrialForm(forms.ModelForm):

    class Meta:
        model = Tester
        fields = [
            "first_name",
            "last_name",
            "birthday",
            "email",
            "telephone",
            "notes",
            "sex",
        ]


class MessageForm(forms.ModelForm):
    autodelete = forms.DateTimeField(
        label="Zeitpunkt der Löschung",
        widget=forms.TextInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )

    class Meta:
        model = Message
        fields = ["title", "message", "autodelete"]


class SpotForm(forms.ModelForm):
    class Meta:
        model = Spot
        fields = ["title", "lat", "long", "outdoor"]


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = [
            "title",
            "short",
            "hinweis",
            "trainer",
            "day",
            "min_age",
            "max_age",
            "start_time",
            "end_time",
            "spot",
        ]


#
#
### WIP
#
#


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
