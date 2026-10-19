from django import forms
from django.contrib.auth.models import User
from members.models import Profile, AdditionalEmail


def date_widget():
    # native date picker; the value must be ISO formatted for type="date"
    return forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class MdcFormMixin:
    """Adds the Material Design input class to every widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            attrs = field.widget.attrs
            attrs.setdefault("class", "mdc-text-field__input")
            attrs.setdefault("aria-labelledby", f"{self[name].id_for_label}-label")
            if isinstance(field.widget, forms.Textarea):
                attrs.update(rows=8, cols=80)


class MemberForm(MdcFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {
            "first_name": "Vorname",
            "last_name": "Nachname",
            "email": "E-Mail-Adresse",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # blank=True on the User model, but we need them for every member
        for name in self.fields:
            self.fields[name].required = True


class ProfileForm(MdcFormMixin, forms.ModelForm):
    # TODO: move these choices to the model
    sex = forms.ChoiceField(
        label="Geschlecht",
        choices=[("", "---------"), ("m", "m"), ("w", "w"), ("d", "d")],
    )
    member_num = forms.CharField(label="Mitgliedsnummer", max_length=30)
    birthday = forms.DateField(label="Geburtsdatum", required=False, widget=date_widget())
    membership_start = forms.DateField(
        label="Beginn der Mitgliedschaft", required=False, widget=date_widget()
    )
    membership_end = forms.DateField(
        label="Kündigung zum", required=False, widget=date_widget()
    )

    class Meta:
        model = Profile
        fields = [
            "birthday",
            "address",
            "telephone",
            "sex",
            "parent",
            "parent_telnr",
            "status",
            "member_num",
            "membership_start",
            "membership_end",
            "mandatsref",
            "zahlungsart",
            "beitrag",
            "notes_trainer",
            "notes_chairman",
        ]
        labels = {
            "telephone": "Telefonnummer",
            "beitrag": "Mitgliedsbeitrag",
            "notes_trainer": "Trainernotizen",
            "notes_chairman": "Vorstandsnotizen",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is None:
            # a new member cannot have cancelled yet
            del self.fields["membership_end"]

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("membership_end"):
            cleaned_data["status"] = "Kündigung"
        elif cleaned_data.get("status") == "Kündigung":
            # new members have no membership_end field, so the error goes on the status there
            field = "membership_end" if "membership_end" in self.fields else "status"
            self.add_error(field, "Bei einer Kündigung muss das Kündigungsdatum gesetzt sein.")
        return cleaned_data

    def clean_member_num(self):
        member_num = self.cleaned_data["member_num"].strip()
        if not member_num.isdigit():
            raise forms.ValidationError("Die Mitgliedsnummer darf nur Ziffern enthalten.")
        taken = Profile.objects.filter(member_num=member_num).exclude(pk=self.instance.pk)
        if taken.exists():
            raise forms.ValidationError("Diese Mitgliedsnummer ist bereits vergeben.")
        return member_num


class AdditionalEmailForm(MdcFormMixin, forms.ModelForm):
    # a CharField on the model, so validate the address here
    email = forms.EmailField(label="Weitere E-Mail-Adresse", max_length=200)

    class Meta:
        model = AdditionalEmail
        fields = ["title", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

    def has_input(self):
        """The fields are optional on the page, so only validate when something was typed."""
        return any(self.data.get(self.add_prefix(name)) for name in self.fields)
