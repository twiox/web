from django import forms
from user_handling.forms import MdcFormMixin, date_widget
from members.models import calculate_age
from .models import Tester

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
        fields = ["first_name", "last_name", "birthday", "sex", "contact_person", "email", "telnr", "notes", "has_consent"]
        labels = {"email": "E-Mail", "notes": "Notizen", "contact_person": "Kontaktperson (bei Minderjährigen)"}
        widgets = {"notes": forms.Textarea}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notes"].widget.attrs["rows"] = 4
        self.fields["has_consent"].widget.attrs.pop("class", None)  # rendered as a chip
        if self.instance.age is not None and self.instance.age >= 18:
            del self.fields["has_consent"]  # only minors need their parents' consent


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
