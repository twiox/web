from django import forms
from user_handling.forms import MdcFormMixin, date_widget
from members.models import calculate_age
from members.models import Session
from trainer.models import TrainingSessionEntry
from .models import Tester, TrialDate, TrialGroup

# the choices of the trial sign-up form on the interested page
SEX_CHOICES = [("weiblich", "weiblich"), ("männlich", "männlich"), ("divers", "divers"), ("keine Angabe", "keine Angabe")]


def minor_needs_contact(form, cleaned_data):
    """Minors are usually signed up by a parent; we need to know who to talk to."""
    birthday, contact = cleaned_data.get("birthday"), cleaned_data.get("contact_person")
    if birthday and calculate_age(birthday) < 18 and not contact:
        form.add_error("contact_person", "Bei Minderjährigen bitte eine Kontaktperson (z.B. ein Elternteil) angeben.")


class ProbetrainingForm(forms.ModelForm):
    """Public trial request on the interested page."""

    confirm = forms.BooleanField()

    class Meta:
        model = Tester
        fields = [
            "first_name",
            "last_name",
            "birthday",
            "contact_person",
            "email",
            "telnr",
            "notes",
            "confirm",
            "sex",
        ]

    def clean(self):
        cleaned_data = super().clean()
        minor_needs_contact(self, cleaned_data)
        return cleaned_data


class TesterForm(MdcFormMixin, forms.ModelForm):
    """Trainers and chairmen correct a trial participant's data."""

    birthday = forms.DateTimeField(label="Geburtsdatum", widget=date_widget())
    sex = forms.ChoiceField(label="Geschlecht", choices=SEX_CHOICES)

    class Meta:
        model = Tester
        fields = [
            "first_name", "last_name", "birthday", "sex", "contact_person", "email", "telnr", "notes", "has_consent",
            "trial_group", "board_notes",
        ]
        labels = {"email": "E-Mail", "notes": "Notizen", "contact_person": "Kontaktperson (bei Minderjährigen)"}
        widgets = {"notes": forms.Textarea, "board_notes": forms.Textarea}

    def __init__(self, *args, board=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notes"].widget.attrs["rows"] = 4
        self.fields["trial_group"].empty_label = "– wartet –"
        if board:
            self.fields["board_notes"].widget.attrs["rows"] = 4
        else:
            del self.fields["board_notes"]  # written by the board, the trainers only read them
        self.fields["has_consent"].widget.attrs.pop("class", None)  # rendered as a chip
        if self.instance.age is not None and self.instance.age >= 18:
            del self.fields["has_consent"]  # only minors need their parents' consent


class TrialGroupForm(MdcFormMixin, forms.ModelForm):
    class Meta:
        model = TrialGroup
        fields = ["name", "notes"]
        labels = {"name": "Name der Gruppe"}
        widgets = {"notes": forms.Textarea}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notes"].widget.attrs["rows"] = 3


class TrialDateForm(MdcFormMixin, forms.ModelForm):
    class Meta:
        model = TrialDate
        fields = ["date", "session"]
        widgets = {"date": date_widget()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        session = self.fields["session"]
        session.queryset = Session.objects.order_by("day_key", "start_time")
        session.label_from_instance = lambda s: f"{s.day} {s.format_start_time} – {s.title}"


class BaseTrialDateFormSet(forms.BaseInlineFormSet):
    """Dates that trainers already entered a training for are locked: their attendance hangs on date and time."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            trial_date = form.instance
            form.locked = bool(trial_date.pk) and TrainingSessionEntry.objects.filter(
                session=trial_date.session_id, date__date=trial_date.date
            ).exists()
            if form.locked:
                form.fields["date"].disabled = True  # the posted values are ignored, the stored ones kept
                form.fields["session"].disabled = True

    def clean(self):
        super().clean()
        for form in self.forms:
            if form.locked and self._should_delete_form(form):
                raise forms.ValidationError(
                    f"Am {form.instance.date:%d.%m.%Y} wurde bereits eine Trainingsstunde erfasst – der Termin kann nicht entfernt werden."
                )


# the dates of a group, edited together with it; empty rows are ignored
TrialDateFormSet = forms.inlineformset_factory(
    TrialGroup, TrialDate, form=TrialDateForm, formset=BaseTrialDateFormSet, extra=1, can_delete=True,
)


class PublicEventForm(forms.Form):
    # user-data
    first_name = forms.CharField()
    last_name = forms.CharField()
    birthday = forms.DateField()
    email = forms.EmailField()
    phone = forms.CharField(required=False)
    contact = forms.CharField(required=False)
    costs = forms.CharField(required=False)
    confirm = forms.BooleanField()
    inform_ok = forms.BooleanField(required=False)
    # merch-data
    merch_wanted = forms.BooleanField(required=False)
    merch_size = forms.CharField(required=False)

    class Meta:
        fields = [
            "first_name",
            "last_name",
            "birthday",
            "email",
            "phone",
            "contact",
            "merch_wanted",
            "merch_size",
            "costs",
            "confirm",
            "inform_ok"
        ]
