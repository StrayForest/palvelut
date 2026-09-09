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
    professional_right_reference = forms.CharField(
        max_length=500,
        required=False,
        help_text=(
            "Required for an employed regulated professional: official register or "
            "professional-right reference."
        ),
    )
    employer_authorization_reference = forms.CharField(
        max_length=500,
        required=False,
        help_text=(
            "Required for an employed regulated professional: employer authorization "
            "to list services."
        ),
    )
    provider_terms_accepted = forms.BooleanField(
        required=True,
        label="I accept the current provider terms",
    )

    def clean_evidence_kind(self):
        value = self.cleaned_data["evidence_kind"]
        if value not in ALLOWED_CLAIM_EVIDENCE:
            raise forms.ValidationError(
                "Independent business-control evidence is required."
            )
        return value


class NewProviderClaimForm(ProviderClaimForm):
    provider_type = forms.ChoiceField(
        choices=(
            (Provider.Type.BUSINESS, "Business / self-employed provider"),
            (Provider.Type.INDIVIDUAL, "Employed regulated professional"),
        )
    )
    legal_name = forms.CharField(max_length=200)
    display_name = forms.CharField(max_length=200)
    y_tunnus = forms.CharField(max_length=16, required=False, label="Y-tunnus")

    field_order = (
        "provider_type",
        "legal_name",
        "display_name",
        "y_tunnus",
        "professional_right_reference",
        "employer_authorization_reference",
        "evidence_kind",
        "evidence_reference",
        "provider_terms_accepted",
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
        provider_type = cleaned.get("provider_type")
        if provider_type == Provider.Type.BUSINESS and not cleaned.get("y_tunnus"):
            self.add_error(
                "y_tunnus", "Y-tunnus is required for a commercial provider."
            )
        if provider_type == Provider.Type.INDIVIDUAL:
            if not cleaned.get("professional_right_reference", "").strip():
                self.add_error(
                    "professional_right_reference",
                    "Official professional-right evidence is required.",
                )
            if not cleaned.get("employer_authorization_reference", "").strip():
                self.add_error(
                    "employer_authorization_reference",
                    "Employer authorization is required.",
                )
        return cleaned


class StaffClaimDecisionForm(forms.Form):
    decision = forms.ChoiceField(
        choices=(("approve", "Approve"), ("reject", "Reject")),
    )
    review_note = forms.CharField(max_length=500, required=False, widget=forms.Textarea)
