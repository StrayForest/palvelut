from django import forms

from .claim_services import ALLOWED_CLAIM_EVIDENCE
from .models import Provider


class ProviderClaimForm(forms.Form):
    evidence_kind = forms.ChoiceField(
        label="Как вы подтверждаете право управлять карточкой",
        choices=(
            ("registry_signatory", "Данные о праве представлять компанию в официальном реестре"),
            ("business_domain_email", "Рабочая почта на домене компании"),
            ("staff_reviewed_equivalent", "Другое подтверждение для ручной проверки"),
        ),
    )
    evidence_reference = forms.CharField(
        max_length=500,
        widget=forms.Textarea,
        label="Ссылка или описание подтверждения",
        help_text="Укажите источник или данные, по которым Finrix сможет проверить ваше право управлять карточкой.",
    )
    professional_right_reference = forms.CharField(
        max_length=500,
        required=False,
        label="Ссылка на профессиональное право",
        help_text=(
            "Нужно для наёмного специалиста регулируемой профессии: ссылка или идентификатор в официальном реестре."
        ),
    )
    employer_authorization_reference = forms.CharField(
        max_length=500,
        required=False,
        label="Подтверждение работодателя",
        help_text=(
            "Нужно для наёмного специалиста регулируемой профессии: подтверждение работодателя, что услуги можно размещать в каталоге."
        ),
    )
    provider_terms_accepted = forms.BooleanField(
        required=True,
        label="Я принимаю действующие условия для специалистов",
    )

    def clean_evidence_kind(self):
        value = self.cleaned_data["evidence_kind"]
        if value not in ALLOWED_CLAIM_EVIDENCE:
            raise forms.ValidationError(
                "Нужно независимое подтверждение права управлять карточкой."
            )
        return value


class NewProviderClaimForm(ProviderClaimForm):
    provider_type = forms.ChoiceField(
        label="Кто оказывает услуги",
        choices=(
            (Provider.Type.BUSINESS, "Компания или предприниматель с Y-tunnus"),
            (Provider.Type.INDIVIDUAL, "Наёмный специалист регулируемой профессии"),
        ),
    )
    legal_name = forms.CharField(max_length=200, label="Юридическое имя или название")
    display_name = forms.CharField(max_length=200, label="Название в каталоге")
    y_tunnus = forms.CharField(
        max_length=16,
        required=False,
        label="Y-tunnus",
        help_text="Обязателен для компании или предпринимателя.",
    )

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
                "Специалист или компания с этим Y-tunnus уже есть. Подтвердите существующую карточку вместо создания новой."
            )
        return value

    def clean(self):
        cleaned = super().clean()
        provider_type = cleaned.get("provider_type")
        if provider_type == Provider.Type.BUSINESS and not cleaned.get("y_tunnus"):
            self.add_error(
                "y_tunnus", "Для компании или предпринимателя нужен Y-tunnus."
            )
        if provider_type == Provider.Type.INDIVIDUAL:
            if not cleaned.get("professional_right_reference", "").strip():
                self.add_error(
                    "professional_right_reference",
                    "Нужно подтверждение профессионального права в официальном источнике.",
                )
            if not cleaned.get("employer_authorization_reference", "").strip():
                self.add_error(
                    "employer_authorization_reference",
                    "Нужно подтверждение работодателя.",
                )
        return cleaned


class StaffClaimDecisionForm(forms.Form):
    decision = forms.ChoiceField(
        choices=(("approve", "Одобрить"), ("reject", "Отклонить")),
        label="Решение",
    )
    review_note = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea,
        label="Комментарий проверки",
    )
