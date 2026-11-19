from datetime import datetime

from django import forms
from django.contrib.auth.forms import PasswordChangeForm
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


# the member's own profile page (profile.py)

class ProfileSelfForm(MdcFormMixin, forms.ModelForm):
    """The data a member keeps up to date on their own profile page."""

    birthday = forms.DateField(label="Geburtsdatum", required=False, widget=date_widget())

    class Meta:
        model = Profile
        fields = ["birthday", "address", "telephone", "parent", "parent_telnr"]
        labels = {
            "address": "Adresse",
            "telephone": "Telefonnummer",
            "parent": "Ansprechpartner*in",
            "parent_telnr": "Notfallnummer",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # optional on the model, but every member needs them
        self.fields["address"].required = True
        self.fields["telephone"].required = True
        self.fields["birthday"].widget.attrs["max"] = datetime.now().strftime("%Y-%m-%d")

    def clean_birthday(self):
        birthday = self.cleaned_data.get("birthday")
        if birthday and birthday > datetime.now().date():
            raise forms.ValidationError("Das Geburtsdatum liegt in der Zukunft.")
        return birthday


class UpdateMemberInformationForm(forms.ModelForm):
    """Message from a member to the board, optionally with one attachment (e.g. a new SEPA mandate)."""

    MAX_ATTACHMENT = 5 * 1024 * 1024  # the page says 5 MB

    comment = forms.CharField(label="Nachricht", widget=forms.Textarea, error_messages={"required": "Bitte schreib eine Nachricht."})
    attachment = forms.FileField(label="Anhang", required=False)

    class Meta:
        model = User
        fields = ["comment", "attachment"]

    def clean_attachment(self):
        attachment = self.cleaned_data.get("attachment")
        if attachment and attachment.size > self.MAX_ATTACHMENT:
            raise forms.ValidationError("Der Anhang ist zu groß (höchstens 5 MB).")
        return attachment


class UpdateMemberEmailForm(MdcFormMixin, forms.Form):
    """New login and contact address; the password confirms it's really the member."""

    password = forms.CharField(label="Dein Passwort", widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))
    email1 = forms.EmailField(label="Neue E-Mail-Adresse", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    email2 = forms.EmailField(label="Neue E-Mail-Adresse wiederholen", widget=forms.EmailInput(attrs={"autocomplete": "email"}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("Das Passwort stimmt nicht.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("email1") and cleaned_data.get("email2") and cleaned_data["email1"] != cleaned_data["email2"]:
            self.add_error("email2", "Die E-Mail-Adressen stimmen nicht überein.")
        return cleaned_data


class UsernameForm(MdcFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["username"]
        labels = {"username": "Nutzername"}


class MemberPasswordChangeForm(MdcFormMixin, PasswordChangeForm):
    """Django's password change form in the site's field style."""
