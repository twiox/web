#we need this to add custom fields to our UserCreationForm
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from members.models import Profile, Group, Trainer, Chairman

class MemberListUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name","last_name","email"]

class MemberListProfileUpdateForm(forms.ModelForm):
    group = forms.ModelChoiceField(label="Gruppe",queryset=Group.objects.all())
    class Meta:
        model = Profile
        fields = ["birthday","address","telephone","sex","status","member_num","group","membership_start","membership_end","mandatsref","zahlungsart",
        "beitrag","notes_trainer","notes_chairman","parent", "parent_telnr"]

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
    group = forms.ModelChoiceField(label="Gruppe",queryset=Group.objects.all())
    
    class Meta:
        model = Profile
        fields = ["birthday","address","telephone","sex","status","member_num","group","membership_start","mandatsref","zahlungsart",
        "beitrag","notes_trainer","notes_chairman","parent", "parent_telnr"]
