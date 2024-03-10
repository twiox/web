# we need this to add custom fields to our UserCreationForm
from django import forms
from members.models import Trainer
from django.contrib.auth.models import User


class TrainerCreationForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        label="Wer?",
        queryset=User.objects.exclude(trainer__user__username__contains=""),
    )

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
            "image",
        ]
