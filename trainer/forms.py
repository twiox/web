from django import forms
from members.models import Trainer
from user_handling.forms import MdcFormMixin, date_widget
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
