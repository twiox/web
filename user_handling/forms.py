#we need this to add custom fields to our UserCreationForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from members.models import Profile, Group, Trainer

class MemberCreationForm(UserCreationForm):
    first_name = forms.CharField(label="Vorname")
    last_name = forms.CharField(label="Nachname")
    email = forms.EmailField(label="Emailadresse") #required, so leave blank
    
    class Meta:
        model = User
        fields = ["username","first_name","last_name","email","password1","password2"]

class ProfileCreationForm(forms.ModelForm):
    member_num = forms.CharField(label="Mitgl.Nr.")
    #make sure, that the group-choices are dynamicly
    group = forms.ModelChoiceField(label="Gruppe",queryset=Group.objects.all())
    
    class Meta:
        model = Profile
        fields = ["member_num", "group"]
        
class TrainerCreationForm(forms.ModelForm):
    user = forms.ModelChoiceField(label="Wer?",queryset=User.objects.all()) #Find a way to filter??
    trainer_telnr = forms.CharField(label = "Öffentliche TelNr.")
    trainer_email = forms.CharField(label = "Öffentliche Email")
    image = forms.ImageField(required=False)
    
    class Meta:
        model = Trainer
        fields = ["user", "trainer_telnr","trainer_email","image"]

    