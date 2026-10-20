from django import forms
from .models import TrainingSessionEntry

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
