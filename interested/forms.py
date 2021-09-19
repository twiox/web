from django import forms

class ProbetrainingForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    birth_date = forms.DateField()
    city = forms.CharField()
    email = forms.EmailField()
    telephone = forms.CharField()
    notes = forms.CharField(required=False)
    confirm = forms.BooleanField()

    class Meta:
        fields = ["first_name", "last_name", "birth_date", "email", "telephone", "notes", "confirm"]


class PublicEventForm(forms.Form):
    #user-data
    first_name = forms.CharField()
    last_name = forms.CharField()
    birthday = forms.DateField()
    email = forms.EmailField()
    phone = forms.CharField()
    contact = forms.CharField(required=False)
    costs = forms.CharField(required=False)
    confirm = forms.BooleanField()
    #merch-data
    merch_wanted = forms.BooleanField(required=False)
    merch_size = forms.CharField(required=False)

    class Meta:
        fields = ["first_name", "last_name", "birthday", "email", "phone", "contact", "merch_wanted", "merch_size", "costs", "confirm"]

