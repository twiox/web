from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm 
from .models import Event, Session, Group, Spot

class SpotForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SpotForm, self).__init__(*args, **kwargs)
        self.fields['description'].strip = False
    
    description = forms.CharField(widget=forms.Textarea)
    
    class Meta:
        model = Spot
        fields = ["title","lat","long","description"]


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
        fields = ["title","place","info_only","costs","start_date","end_date","deadline","hinweis","description",
            "allowed_groups","teilnahmebedingungen", "datenschutz", "einverstaendnis"]
        widgets = {
            'allowed_groups': forms.CheckboxSelectMultiple,
        }

class EventUpdateParticipantForm(forms.ModelForm):
    confirm = forms.BooleanField()
    telnr = forms.CharField()
    email = forms.EmailField()
    birthday = forms.DateField()
    class Meta:
        model=Event
        fields = ["email","telnr","birthday","confirm"]
 
class EventUpdateParticipantForm2(forms.ModelForm):
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
    password = forms.CharField(widget=forms.PasswordInput)
    email1 = forms.EmailField()
    email2 = forms.EmailField()
    class Meta:
        model = User
        fields = ["password", "email1", "email2"]