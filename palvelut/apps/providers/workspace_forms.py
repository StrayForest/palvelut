from django import forms

from palvelut.apps.providers.models import Provider


class ProviderProfileForm(forms.Form):
    provider_type = forms.ChoiceField(choices=Provider.Type.choices)
    legal_name = forms.CharField(max_length=200)
    display_name = forms.CharField(max_length=200)
    y_tunnus = forms.CharField(max_length=16, required=False)

    def cleaned_payload(self) -> dict[str, str]:
        if not self.is_valid():
            raise ValueError("form must be valid before reading payload")
        return {
            "provider_type": self.cleaned_data["provider_type"],
            "legal_name": self.cleaned_data["legal_name"].strip(),
            "display_name": self.cleaned_data["display_name"].strip(),
            "y_tunnus": self.cleaned_data["y_tunnus"].strip(),
        }
