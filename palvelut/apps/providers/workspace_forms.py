from __future__ import annotations

from typing import Any

from django import forms

from palvelut.apps.providers.models import ContactChannel, Provider, ServiceArea
from palvelut.apps.taxonomy.models import Category, Language, Municipality


class ProviderProfileForm(forms.Form):
    provider_type = forms.ChoiceField(choices=Provider.Type.choices)
    legal_name = forms.CharField(max_length=200)
    display_name = forms.CharField(max_length=200)
    y_tunnus = forms.CharField(max_length=16, required=False)
    contacts = forms.JSONField(required=False, initial=list, widget=forms.Textarea)
    services = forms.JSONField(required=False, initial=list, widget=forms.Textarea)
    service_areas = forms.JSONField(
        required=False,
        initial=list,
        widget=forms.Textarea,
    )
    languages = forms.JSONField(required=False, initial=list, widget=forms.Textarea)

    def _list_of_dicts(self, field: str) -> list[dict[str, Any]]:
        value = self.cleaned_data.get(field) or []
        if not isinstance(value, list) or any(
            not isinstance(item, dict) for item in value
        ):
            raise forms.ValidationError("Enter a JSON list of objects.")
        return value

    def clean_contacts(self) -> list[dict[str, Any]]:
        items = self._list_of_dicts("contacts")
        allowed = set(ContactChannel.Kind.values)
        normalized: list[dict[str, Any]] = []
        for item in items:
            kind = str(item.get("kind", "")).strip()
            value = str(item.get("value", "")).strip()
            if kind not in allowed or not value:
                raise forms.ValidationError(
                    "Each contact needs a supported kind and value."
                )
            normalized.append(
                {
                    "kind": kind,
                    "value": value[:500],
                    "label": str(item.get("label", "")).strip()[:80],
                    "is_public": bool(item.get("is_public", True)),
                    "sort_order": max(0, int(item.get("sort_order", 0))),
                }
            )
        return normalized

    def clean_services(self) -> list[dict[str, Any]]:
        items = self._list_of_dicts("services")
        category_ids = {str(item.get("category_id", "")).strip() for item in items}
        category_ids.discard("")
        known = set(
            Category.objects.filter(pk__in=category_ids).values_list("pk", flat=True)
        )
        if {str(pk) for pk in known} != category_ids:
            raise forms.ValidationError("Unknown service category.")
        normalized: list[dict[str, Any]] = []
        for item in items:
            category_id = str(item.get("category_id", "")).strip()
            if not category_id:
                raise forms.ValidationError("Each service needs category_id.")
            normalized.append(
                {
                    "category_id": category_id,
                    "title": str(item.get("title", "")).strip()[:160],
                    "description": str(item.get("description", "")).strip(),
                    "price_text": str(item.get("price_text", "")).strip()[:160],
                    "is_active": bool(item.get("is_active", True)),
                }
            )
        return normalized

    def clean_service_areas(self) -> list[dict[str, Any]]:
        items = self._list_of_dicts("service_areas")
        municipality_ids = {
            str(item.get("municipality_id", "")).strip() for item in items
        }
        municipality_ids.discard("")
        known = set(
            Municipality.objects.filter(pk__in=municipality_ids).values_list(
                "pk", flat=True
            )
        )
        if {str(pk) for pk in known} != municipality_ids:
            raise forms.ValidationError("Unknown municipality.")
        allowed_modes = set(ServiceArea.Mode.values)
        normalized: list[dict[str, Any]] = []
        for item in items:
            municipality_id = str(item.get("municipality_id", "")).strip()
            mode = str(item.get("mode", "")).strip()
            if not municipality_id or mode not in allowed_modes:
                raise forms.ValidationError(
                    "Each service area needs municipality_id and mode."
                )
            normalized.append({"municipality_id": municipality_id, "mode": mode})
        return normalized

    def clean_languages(self) -> list[dict[str, Any]]:
        items = self._list_of_dicts("languages")
        language_ids = {str(item.get("language_id", "")).strip() for item in items}
        language_ids.discard("")
        known = set(
            Language.objects.filter(pk__in=language_ids).values_list("pk", flat=True)
        )
        if {str(pk) for pk in known} != language_ids:
            raise forms.ValidationError("Unknown language.")
        return [
            {
                "language_id": str(item.get("language_id", "")).strip(),
                "declared": bool(item.get("declared", True)),
            }
            for item in items
        ]

    def cleaned_payload(self) -> dict[str, Any]:
        if not self.is_valid():
            raise ValueError("form must be valid before reading payload")
        return {
            "provider_type": self.cleaned_data["provider_type"],
            "legal_name": self.cleaned_data["legal_name"].strip(),
            "display_name": self.cleaned_data["display_name"].strip(),
            "y_tunnus": self.cleaned_data["y_tunnus"].strip(),
            "contacts": self.cleaned_data["contacts"],
            "services": self.cleaned_data["services"],
            "service_areas": self.cleaned_data["service_areas"],
            "languages": self.cleaned_data["languages"],
        }
