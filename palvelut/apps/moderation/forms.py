from django import forms


class ContentReportForm(forms.Form):
    category = forms.ChoiceField(
        choices=(
            ("incorrect_content", "Incorrect or outdated content"),
            ("impersonation", "Impersonation or ownership concern"),
            ("illegal_or_harmful", "Illegal or harmful content"),
            ("other", "Other"),
        )
    )
    details = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={"rows": 6}))


class ReportStatusForm(forms.Form):
    status_token = forms.CharField(max_length=200, strip=True)


class StaffContentCaseForm(forms.Form):
    action = forms.ChoiceField(
        choices=(
            ("notice", "Send provider notice"),
            ("resolve", "Resolve"),
            ("dismiss", "Dismiss"),
        )
    )
    note = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={"rows": 5}))


class ProviderAppealForm(forms.Form):
    note = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={"rows": 5}))
