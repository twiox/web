from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Event, Session, Group, Spot, Document


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
        fields = ["title", "day", "start_time", "end_time", "hinweis", "spot", "trainer", "agegroup"]
        widgets = {
            "trainer": forms.CheckboxSelectMultiple,
        }


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "place",
            "info_only",
            "costs",
            "start_date",
            "end_date",
            "deadline",
            "hinweis",
            "description",
            "allowed_agegroups",
            "teilnahmebedingungen",
            "datenschutz",
            "einverstaendnis",
        ]
        widgets = {
            "allowed_agegroups": forms.CheckboxSelectMultiple,
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
