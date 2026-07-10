from django import forms

from apps.suspects.models import Suspect


INPUT_CLASS = "lg-input"


class SuspectForm(forms.ModelForm):
    class Meta:
        model = Suspect
        fields = ["national_id", "full_name", "aliases", "date_of_birth", "notes"]
        widgets = {
            "national_id": forms.TextInput(attrs={"class": INPUT_CLASS, "autocomplete": "off"}),
            "full_name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "aliases": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "date_of_birth": forms.DateInput(attrs={"class": INPUT_CLASS, "type": "date"}),
            "notes": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 4}),
        }
