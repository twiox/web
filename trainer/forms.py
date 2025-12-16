#we need this to add custom fields to our UserCreationForm
from django import forms
from members.models import Trainer, Group
from .models import TrainingSessionEntry
from django.contrib.auth.models import User

class TrainingSessionForm(forms.ModelForm):
    class Meta:
        model = TrainingSessionEntry
        fields = [
            'date',
            'session',
            'group',
            'start',
            'end',
            'notes'
        ]

class TrainerCreationForm(forms.ModelForm):
    user = forms.ModelChoiceField(label="Wer?",queryset=User.objects.exclude(trainer__user__username__contains=""))

    class Meta:
        model = Trainer
        fields = [
        "user",
        "trainer_telnr",
        "trainer_email",
        "license_number",
        "license_valid",
        "license_level",
        "contract",
        "license",
        "codex",
        "salary",
        "image"
        ]


class TrainerDeletionForm(forms.Form):
    trainer = forms.ModelChoiceField(label="Wer?",queryset=Trainer.objects.all())
    group = forms.ModelChoiceField(label="In welche Gruppe verschieben?",queryset=Group.objects.all())
    class Meta:
        fields = ["trainer", "group"]


class TrainerChooseForm(forms.Form):
    trainer = forms.ModelChoiceField(label="Wer?",queryset=Trainer.objects.all())
    class Meta:
        fields = ["trainer"]
