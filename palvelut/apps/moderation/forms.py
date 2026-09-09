from django import forms
from django.utils.translation import gettext_lazy as _

from .models import DataSubjectRequest


class ContentReportForm(forms.Form):
    category = forms.ChoiceField(
        label=_("What is the problem?"),
        choices=(
            ("incorrect_content", _("Incorrect or outdated information")),
            ("impersonation", _("Impersonation or ownership concern")),
            ("illegal_or_harmful", _("Suspected illegal or harmful content")),
            ("other", _("Other directory-policy concern")),
        ),
    )
    details = forms.CharField(
        label=_("Details"),
        help_text=_(
            "Explain what should be reviewed and why. Do not include unnecessary sensitive personal data."
        ),
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 6}),
    )


class ReportStatusForm(forms.Form):
    status_token = forms.CharField(
        label=_("Private status code"), max_length=200, strip=True
    )


class StaffContentCaseForm(forms.Form):
    action = forms.ChoiceField(
        choices=(
            ("notice", _("Send provider notice")),
            ("resolve", _("Resolve")),
            ("dismiss", _("Dismiss")),
        )
    )
    note = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 5}),
        label=_("Review note"),
    )


class ProviderAppealForm(forms.Form):
    note = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 5}),
        label=_("Appeal or clarification"),
    )


class DataSubjectRequestForm(forms.Form):
    kind = forms.ChoiceField(choices=DataSubjectRequest.Kind.choices)
    note = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )


class StaffDataSubjectRequestForm(forms.Form):
    action = forms.ChoiceField(
        choices=(
            ("start", "Start processing"),
            ("complete", "Mark completed"),
            ("reject", "Reject"),
        )
    )
    note = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={"rows": 5}))
