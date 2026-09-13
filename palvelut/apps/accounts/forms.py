from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)


class ProviderRegistrationForm(UserCreationForm):
    email = forms.EmailField(label="Электронная почта")

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        existing = get_user_model().objects.filter(email__iexact=email).first()
        if existing is not None:
            if existing.is_active:
                raise forms.ValidationError(
                    "Аккаунт с этой электронной почтой уже существует."
                )
            self.existing_unverified_user = existing
        return email

    def save(self, commit=True):
        existing = getattr(self, "existing_unverified_user", None)
        if existing is not None:
            if not settings.ACCOUNT_EMAIL_VERIFICATION_REQUIRED and not existing.is_active:
                existing.is_active = True
                if commit:
                    existing.save(update_fields=["is_active"])
            return existing

        user = super().save(commit=False)
        user.username = self.cleaned_data["email"].strip().lower()
        user.email = user.username
        user.is_active = not settings.ACCOUNT_EMAIL_VERIFICATION_REQUIRED
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Электронная почта")


class RateLimitedPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="Электронная почта")


class SecureSetPasswordForm(SetPasswordForm):
    pass


class MFAForm(forms.Form):
    code = forms.CharField(min_length=6, max_length=6, label="Код")
