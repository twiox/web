from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm 
from .models import Event, Session, Group


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields=["title","day","start_time","end_time","hinweis","spot","trainer","group"]
        widgets = {
            'trainer': forms.CheckboxSelectMultiple,
        }

class EventForm(forms.ModelForm):
    #allowed_groups = forms.ModelChoiceField(label="Für die Gruppen?",queryset=Group.objects.exclude(group_id = "T"))
    class Meta:
        model = Event
        fields = ["title","start_date","end_date","deadline","hinweis","description","allowed_groups"]
        widgets = {
            'allowed_groups': forms.CheckboxSelectMultiple,
        }


class EventUpdateParticipantForm(forms.ModelForm):
    class Meta:
        model=Event
        fields = []
        

class UpdateMemberInformationForm(forms.Form):
    
    name = forms.CharField(label='Dein Name*', max_length=100)
    post_adress = forms.CharField(label='Deine (neue) Adresse', max_length=100, required=False)
    email = forms.EmailField(label='Deine (neue) Emailadresse', required=False)
    comments = forms.CharField(label="Kommentar", required = False,  max_length=140)
    bankaccount = forms.BooleanField(label='Neues Bankkonto', required=False)
    attachment = forms.FileField(label="Anhänge", required=False)
        
    class Meta:
        fields = ["name", "post_adress", "email", "bankaccount", "attachment"]