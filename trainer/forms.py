from datetime import date, timedelta
from django import forms
from members.models import Trainer
from user_handling.forms import MdcFormMixin, date_widget
from .models import TrainingSessionEntry

def minutes(value):
    """ "17:30" -> 1050; None for an empty or odd time (the times are free text fields)."""
    try:
        hours, mins = str(value).strip().split(":")[:2]
        return int(hours) * 60 + int(mins)
    except (ValueError, AttributeError):
        return None


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

    def duplicate(self):
        """An existing entry for the same training on the same day with overlapping times, or None.
        Same training: the same training time, or without one the same group name."""
        data = self.cleaned_data
        day, session, group = data.get("date"), data.get("session"), (data.get("group") or "").strip()
        if not day:
            return None
        candidates = TrainingSessionEntry.objects.filter(date__date=day.date()).exclude(pk=self.instance.pk)
        if session:
            candidates = candidates.filter(session=session)
        elif group:
            candidates = candidates.filter(session__isnull=True, group__iexact=group)
        else:
            return None
        start, end = minutes(data.get("start")), minutes(data.get("end"))
        for entry in candidates.order_by("pk"):
            other_start, other_end = minutes(entry.start), minutes(entry.end)
            # without complete times, the same training on the same day counts as the same entry
            if None in (start, end, other_start, other_end) or (start < other_end and other_start < end):
                return entry
        return None

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
