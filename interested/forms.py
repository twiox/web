from django import forms
from .models import Tester


class ProbetrainingForm(forms.ModelForm):
    confirm = forms.BooleanField()

    class Meta:
        model = Tester
        fields = [
            "first_name",
            "last_name",
            "birthday",
            "email",
            "telnr",
            "notes",
            "confirm",
            "sex",
        ]
