from django import forms
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


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ["title", "day", "start_time", "end_time", "hinweis", "spot", "trainer", "min_age", "max_age"]
        widgets = {
            "trainer": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["trainer"].queryset = Trainer.objects.filter(active=True)


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
