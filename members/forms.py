from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm 
from .models import Trainer, Profile, Group
    
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model=User
        fields=['username', 'email']

class TrainerUpdateForm(forms.ModelForm):
    trainer_email = forms.EmailField()
    trainer_telnr = forms.CharField()
    
    class Meta:
        model=Trainer
        fields = ["trainer_telnr", "trainer_email"]

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model=Profile
        fields = [""]

