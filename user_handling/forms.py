#we need this to add custom fields to our UserCreationForm
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from members.models import Profile, Group, Trainer, Chairman

class MemberCreationForm(UserCreationForm):
    first_name = forms.CharField(label="Vorname")
    last_name = forms.CharField(label="Nachname")
    email = forms.EmailField(label="Emailadresse") #required, so leave blank
    
    def __init__(self, *args, **kwargs):
        super(MemberCreationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        self.fields['password1'].widget.attrs['autocomplete'] = 'off'
        self.fields['password2'].widget.attrs['autocomplete'] = 'off'
    
    class Meta:
        model = User
        fields = ["first_name","last_name","email"]

class ProfileCreationForm(forms.ModelForm):
    member_num = forms.CharField(label="Mitgl.Nr.")
    #make sure, that the group-choices are dynamicly
    group = forms.ModelChoiceField(label="Gruppe",queryset=Group.objects.all())
    
    class Meta:
        model = Profile
        fields = ["member_num", "group"]
        
class TrainerCreationForm(forms.ModelForm):
    user = forms.ModelChoiceField(label="Wer?",queryset=User.objects.exclude(trainer__user__username__contains=""))
    trainer_telnr = forms.CharField(label = "Öffentliche TelNr.")
    trainer_email = forms.CharField(label = "Öffentliche Email")
    image = forms.ImageField(label="Profilbild")
    
    class Meta:
        model = Trainer
        fields = ["user", "trainer_telnr","trainer_email","image"]

class TrainerDeletionForm(forms.Form):
    trainer = forms.ModelChoiceField(label="Wer?",queryset=Trainer.objects.all())
    group = forms.ModelChoiceField(label="In welche Gruppe verschieben?",queryset=Group.objects.all())
    class Meta:
        fields = ["trainer", "group"]

class TrainerChooseForm(forms.Form):
    trainer = forms.ModelChoiceField(label="Wer?",queryset=Trainer.objects.all())
    class Meta:
        fields = ["trainer"]