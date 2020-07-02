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
        

class UpdateMemberInformationForm(forms.ModelForm):
    comment = forms.CharField(label="Kommentar", widget=forms.Textarea, required=False)
    attachment = forms.FileField(label="Anhänge", required=False)
    class Meta:
        model = User
        fields = ["comment", "attachment"]
        
class UpdateMemberEmailForm(forms.ModelForm):
    email1 = forms.EmailField()
    email2 = forms.EmailField()
    class Meta:
        model = User
        fields = ["email1", "email2"]