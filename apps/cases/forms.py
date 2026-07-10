from django import forms

from apps.cases.models import Case, EvidenceItem, MOTagOption, Witness
from apps.suspects.models import Suspect


INPUT_CLASS = "lg-input"


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = [
            "case_number",
            "title",
            "crime_category",
            "location",
            "narrative",
            "status",
        ]
        widgets = {
            "case_number": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "title": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "crime_category": forms.Select(attrs={"class": INPUT_CLASS}),
            "location": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "narrative": forms.Textarea(attrs={"rows": 4, "class": INPUT_CLASS}),
            "status": forms.Select(attrs={"class": INPUT_CLASS}),
        }


class MOTagForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for option in MOTagOption.objects.filter(is_active=True).order_by("category", "label"):
            field_name = f"mo_{option.category}"
            if field_name not in self.fields:
                self.fields[field_name] = forms.ChoiceField(
                    label=option.get_category_display(),
                    choices=[("", "— Select —")],
                    required=False,
                    widget=forms.Select(attrs={"class": INPUT_CLASS}),
                )
            choices = list(self.fields[field_name].choices)
            choices.append((option.value, option.label))
            self.fields[field_name].choices = choices

    def cleaned_mo_tags(self):
        tags = {}
        for name, value in self.cleaned_data.items():
            if name.startswith("mo_") and value:
                category = name.replace("mo_", "")
                tags[category] = value
        return tags


class SuspectLinkForm(forms.Form):
    national_id = forms.CharField(max_length=32, label="National ID")
    full_name = forms.CharField(max_length=128, required=False)
    role = forms.CharField(max_length=64, initial="suspect")

    def resolve_suspect(self):
        national_id = self.cleaned_data["national_id"].strip()
        suspect, _created = Suspect.objects.get_or_create(
            national_id=national_id,
            defaults={"full_name": self.cleaned_data.get("full_name") or national_id},
        )
        if self.cleaned_data.get("full_name") and suspect.full_name != self.cleaned_data["full_name"]:
            suspect.full_name = self.cleaned_data["full_name"]
            suspect.save(update_fields=["full_name", "updated_at"])
        return suspect


class WitnessForm(forms.ModelForm):
    class Meta:
        model = Witness
        fields = ["full_name", "contact", "statement"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Witness full name"}),
            "contact": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Phone or email"}),
            "statement": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 3, "placeholder": "Statement summary"}),
        }


class EvidenceForm(forms.ModelForm):
    class Meta:
        model = EvidenceItem
        fields = ["label", "description", "storage_path"]
        widgets = {
            "label": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "e.g. CCTV footage"}),
            "description": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 2}),
            "storage_path": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Chain-of-custody path / reference"}),
        }
