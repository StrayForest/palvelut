from django import forms

from .claim_services import ALLOWED_CLAIM_EVIDENCE


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
            raise forms.ValidationError("Independent business-control evidence is required.")
        return value


class StaffClaimDecisionForm(forms.Form):
    decision = forms.ChoiceField(choices=(("approve", "Approve"), ("reject", "Reject")))
    review_note = forms.CharField(max_length=500, required=False, widget=forms.Textarea)
