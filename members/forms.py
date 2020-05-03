from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm 
from .models import Event

class GetSessionForm(forms.ModelForm):
    class Meta:
        fields = []

class EventUpdateParticipantForm(forms.ModelForm):
    class Meta:
        model=Event
        fields = []

