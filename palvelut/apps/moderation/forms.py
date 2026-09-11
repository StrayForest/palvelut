from django import forms

from .models import DataSubjectRequest


class ContentReportForm(forms.Form):
    category = forms.ChoiceField(
        label="В чём проблема?",
        choices=(
            ("incorrect_content", "Неточная или устаревшая информация"),
            (
                "impersonation",
                "Выдача себя за другое лицо или спор о праве на карточку",
            ),
            (
                "illegal_or_harmful",
                "Предположительно незаконное или вредоносное содержание",
            ),
            ("other", "Другая проблема с правилами каталога"),
        ),
    )
    details = forms.CharField(
        label="Подробности",
        help_text=(
            "Опишите, что нужно проверить и почему. Не указывайте лишние чувствительные персональные данные."
        ),
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 6}),
    )


class ReportStatusForm(forms.Form):
    status_token = forms.CharField(
        label="Приватный код статуса", max_length=200, strip=True
    )


class StaffContentCaseForm(forms.Form):
    action = forms.ChoiceField(
        label="Действие",
        choices=(
            ("notice", "Отправить уведомление специалисту"),
            ("resolve", "Закрыть как решённую"),
            ("dismiss", "Отклонить жалобу"),
        ),
    )
    note = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 5}),
        label="Комментарий проверки",
    )


class ProviderAppealForm(forms.Form):
    note = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 5}),
        label="Обращение или уточнение",
    )


class DataSubjectRequestForm(forms.Form):
    kind = forms.ChoiceField(
        label="Тип запроса",
        choices=(
            (DataSubjectRequest.Kind.ACCESS, "Доступ к данным"),
            (DataSubjectRequest.Kind.EXPORT, "Экспорт данных"),
            (DataSubjectRequest.Kind.DELETE, "Удаление данных"),
        ),
    )
    note = forms.CharField(
        label="Комментарий",
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )


class StaffDataSubjectRequestForm(forms.Form):
    action = forms.ChoiceField(
        label="Действие",
        choices=(
            ("start", "Начать обработку"),
            ("complete", "Отметить выполненным"),
            ("reject", "Отклонить"),
        ),
    )
    note = forms.CharField(
        label="Комментарий",
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 5}),
    )
