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
        ]
