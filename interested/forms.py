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