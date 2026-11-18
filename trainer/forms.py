from datetime import date, timedelta
from django import forms
from members.models import Trainer
from user_handling.forms import MdcFormMixin, date_widget
from .models import TrainingSessionEntry

class TrainingSessionForm(forms.ModelForm):
    # trainers may only enter sessions up to this far back; chairmen may enter any date
    MAX_AGE = timedelta(weeks=4)

    def __init__(self, *args, allow_old_dates=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_old_dates = allow_old_dates

    @classmethod
    def min_date(cls):
        return date.today() - cls.MAX_AGE

    def clean_date(self):
        value = self.cleaned_data["date"]
        # an unchanged date stays editable, so trainers can still fix e.g. the group of an older entry
        date_set = self.instance.pk is None or "date" in self.changed_data
        if value and date_set and not self.allow_old_dates and value.date() < self.min_date():
            raise forms.ValidationError(
                "Einheiten, die länger als 4 Wochen zurückliegen, kann nur der Vorstand eintragen."
            )
        return value

    class Meta:
        model = TrainingSessionEntry
        fields = [
            'date',
            'session',
            'group',
            'start',
            'end',
        ]  # notes are edited on the detail page


class TrainerForm(MdcFormMixin, forms.ModelForm):
    """Edited by the board; trainers use TrainerSelfForm, which has no TAE rate."""

    license_valid = forms.DateField(label="Lizenz gültig bis", required=False, widget=date_widget())
    trainer_email = forms.EmailField(label="Öffentliche E-Mail-Adresse", required=False, empty_value=None)

    class Meta:
        model = Trainer
        fields = [
            "trainer_telnr", "trainer_email",
            "license_level", "license_number", "license_valid", "salary",
            "image", "contract", "license", "codex",
        ]
        labels = {
            "trainer_telnr": "Öffentliche Telefonnummer",
            "license_level": "Lizenzstufe",
            "license_number": "Lizenznummer",
            "salary": "TAE pro Stunde (€)",
            "image": "Profilbild",
            "contract": "Vertrag",
            "license": "Lizenz",
            "codex": "Ehrenkodex",
        }
        widgets = {
            # plain file inputs: no "currently / clear" text, the template shows the current file
            "image": forms.FileInput, "contract": forms.FileInput,
            "license": forms.FileInput, "codex": forms.FileInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.pop("class", None)

    @property
    def file_fields(self):
        return [self[name] for name in ["image", "contract", "license", "codex"]]


class TrainerSelfForm(TrainerForm):
    class Meta(TrainerForm.Meta):
        fields = [name for name in TrainerForm.Meta.fields if name != "salary"]


class GroupEmailForm(MdcFormMixin, forms.Form):
    """E-mail from the group page to everyone on a training time's list."""

    subject = forms.CharField(label="Betreff", max_length=150)
    body = forms.CharField(label="Nachricht", widget=forms.Textarea)
    notice = forms.BooleanField(label="Auch als Hinweis bei dieser Trainingszeit anzeigen (3 Tage)", required=False)

    # who else gets it (board, trainers); offered by the view, removable as chips in the form
    info_to = forms.MultipleChoiceField(required=False, widget=forms.MultipleHiddenInput)

    def __init__(self, *args, can_notice=False, info_choices=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["info_to"].choices = [(address, name) for name, address in info_choices]
        self.fields["notice"].widget.attrs.pop("class", None)  # rendered as a chip
        if not can_notice:
            del self.fields["notice"]
