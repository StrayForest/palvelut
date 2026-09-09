from django import forms

from .claim_services import ALLOWED_CLAIM_EVIDENCE
from .models import Provider


class ProviderClaimForm(forms.Form):
    evidence_kind = forms.ChoiceField(
        choices=(
            ("registry_signatory", "Registry signatory evidence"),
            ("business_domain_email", "Matching business-domain email"),
            ("staff_reviewed_equivalent", "Equivalent evidence for staff review"),
        )
    )
    evidence_reference = forms.CharField(max_length=500, widget=forms.Textarea)

    def clean_evidence_kind(self):
        value = self.cleaned_data["evidence_kind"]
        if value not in ALLOWED_CLAIM_EVIDENCE:
            raise forms.ValidationError(
                "Independent business-control evidence is required."
            )
        return value


class NewProviderClaimForm(ProviderClaimForm):
    provider_type = forms.ChoiceField(choices=Provider.Type.choices)
    legal_name = forms.CharField(max_length=200)
    display_name = forms.CharField(max_length=200)
    y_tunnus = forms.CharField(max_length=16, required=False, label="Y-tunnus")

    field_order = (
        "provider_type",
        "legal_name",
        "display_name",
        "y_tunnus",
        "evidence_kind",
        "evidence_reference",
    )

    def clean_y_tunnus(self):
        value = self.cleaned_data.get("y_tunnus", "").strip()
        if value and Provider.objects.filter(y_tunnus=value).exists():
            raise forms.ValidationError(
                "A provider with this Y-tunnus already exists. "
                "Claim the existing profile instead."
            )
        return value

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("provider_type") == Provider.Type.BUSINESS and not cleaned.get(
            "y_tunnus"
        ):
            self.add_error("y_tunnus", "Y-tunnus is required for a business provider.")
        return cleaned


class StaffClaimDecisionForm(forms.Form):
    decision = forms.ChoiceField(
        choices=(("approve", "Approve"), ("reject", "Reject")),
    )
    review_note = forms.CharField(max_length=500, required=False, widget=forms.Textarea)
