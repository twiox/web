from django import forms

class OrganizerForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    telephone = forms.CharField()
    notes = forms.CharField(required=False)
    confirm = forms.BooleanField()
    
    class Meta:
        fields = ["first_name", "last_name", "email", "telephone", "notes", "confirm"]