from django import forms
from django.utils.translation import gettext_lazy as _

from .claim_services import ALLOWED_CLAIM_EVIDENCE
from .models import Provider


class ProviderClaimForm(forms.Form):
    evidence_kind = forms.ChoiceField(
        label=_("Evidence kind"),
        choices=(
            ("registry_signatory", _("Registry signatory evidence")),
            ("business_domain_email", _("Matching business-domain email")),
            ("staff_reviewed_equivalent", _("Equivalent evidence for staff review")),
        ),
    )
    evidence_reference = forms.CharField(
        max_length=500,
        widget=forms.Textarea,
        label=_("Evidence reference"),
    )
    professional_right_reference = forms.CharField(
        max_length=500,
        required=False,
        label=_("Professional-right reference"),
        help_text=_(
            "Required for an employed regulated professional: official register or professional-right reference."
        ),
    )
    employer_authorization_reference = forms.CharField(
        max_length=500,
        required=False,
        label=_("Employer authorization reference"),
        help_text=_(
            "Required for an employed regulated professional: employer authorization to list services."
        ),
    )
    provider_terms_accepted = forms.BooleanField(
        required=True,
        label=_("I accept the current provider terms"),
    )

    def clean_evidence_kind(self):
        value = self.cleaned_data["evidence_kind"]
        if value not in ALLOWED_CLAIM_EVIDENCE:
            raise forms.ValidationError(
                _("Independent business-control evidence is required.")
            )
        return value


class NewProviderClaimForm(ProviderClaimForm):
    provider_type = forms.ChoiceField(
        label=_("Provider type"),
        choices=(
            (Provider.Type.BUSINESS, _("Business / self-employed provider")),
            (Provider.Type.INDIVIDUAL, _("Employed regulated professional")),
        ),
    )
    legal_name = forms.CharField(max_length=200, label=_("Legal name"))
    display_name = forms.CharField(max_length=200, label=_("Display name"))
    y_tunnus = forms.CharField(max_length=16, required=False, label=_("Y-tunnus"))

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
                _(
                    "A provider with this Y-tunnus already exists. Claim the existing profile instead."
                )
            )
        return value

    def clean(self):
        cleaned = super().clean()
        provider_type = cleaned.get("provider_type")
        if provider_type == Provider.Type.BUSINESS and not cleaned.get("y_tunnus"):
            self.add_error(
                "y_tunnus", _("Y-tunnus is required for a commercial provider.")
            )
        if provider_type == Provider.Type.INDIVIDUAL:
            if not cleaned.get("professional_right_reference", "").strip():
                self.add_error(
                    "professional_right_reference",
                    _("Official professional-right evidence is required."),
                )
            if not cleaned.get("employer_authorization_reference", "").strip():
                self.add_error(
                    "employer_authorization_reference",
                    _("Employer authorization is required."),
                )
        return cleaned


class StaffClaimDecisionForm(forms.Form):
    decision = forms.ChoiceField(
        choices=(("approve", _("Approve")), ("reject", _("Reject"))),
    )
    review_note = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea,
        label=_("Review note"),
    )
