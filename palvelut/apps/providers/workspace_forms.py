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

    primary_category = forms.ModelChoiceField(
        queryset=Category.objects.order_by("name"),
        required=False,
        empty_label="Choose a service",
    )
    service_title = forms.CharField(max_length=160, required=False)
    service_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    price_text = forms.CharField(max_length=160, required=False)
    primary_municipality = forms.ModelChoiceField(
        queryset=Municipality.objects.filter(region__country__code="FI").order_by(
            "name"
        ),
        required=False,
        empty_label="Choose a city",
    )
    service_mode = forms.ChoiceField(
        choices=(("", "Choose how you work"), *ServiceArea.Mode.choices),
        required=False,
    )
    service_language = forms.ModelChoiceField(
        queryset=Language.objects.order_by("name"),
        required=False,
        empty_label="Choose a language",
    )
    contact_kind = forms.ChoiceField(
        choices=(("", "Choose a contact method"), *ContactChannel.Kind.choices),
        required=False,
    )
    contact_value = forms.CharField(max_length=500, required=False)

    # Kept for backwards-compatible service/tests and future advanced editing. The
    # provider-facing template uses the normal fields above instead of exposing JSON.
    contacts = forms.JSONField(required=False, initial=list, widget=forms.HiddenInput)
    services = forms.JSONField(required=False, initial=list, widget=forms.HiddenInput)
    service_areas = forms.JSONField(
        required=False,
        initial=list,
        widget=forms.HiddenInput,
    )
    languages = forms.JSONField(required=False, initial=list, widget=forms.HiddenInput)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        initial = dict(kwargs.get("initial") or {})
        self._seed_friendly_initial(initial)
        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    @staticmethod
    def _first(payload: dict[str, Any], field: str) -> dict[str, Any]:
        items = payload.get(field) or []
        if isinstance(items, list) and items and isinstance(items[0], dict):
            return items[0]
        return {}

    def _seed_friendly_initial(self, payload: dict[str, Any]) -> None:
        service = self._first(payload, "services")
        area = self._first(payload, "service_areas")
        language = self._first(payload, "languages")
        contact = self._first(payload, "contacts")
        initial_values = {
            "primary_category": service.get("category_id"),
            "service_title": service.get("title", ""),
            "service_description": service.get("description", ""),
            "price_text": service.get("price_text", ""),
            "primary_municipality": area.get("municipality_id"),
            "service_mode": area.get("mode", ""),
            "service_language": language.get("language_id"),
            "contact_kind": contact.get("kind", ""),
            "contact_value": contact.get("value", ""),
        }
        for field, value in initial_values.items():
            payload.setdefault(field, value)

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

    def _friendly_structured_payload(self) -> dict[str, list[dict[str, Any]]]:
        category = self.cleaned_data.get("primary_category")
        municipality = self.cleaned_data.get("primary_municipality")
        language = self.cleaned_data.get("service_language")
        mode = str(self.cleaned_data.get("service_mode") or "")
        contact_kind = str(self.cleaned_data.get("contact_kind") or "")
        contact_value = str(self.cleaned_data.get("contact_value") or "").strip()

        services = list(self.cleaned_data.get("services") or [])
        if not services and category is not None:
            services = [
                {
                    "category_id": str(category.pk),
                    "title": str(self.cleaned_data.get("service_title") or "").strip(),
                    "description": str(
                        self.cleaned_data.get("service_description") or ""
                    ).strip(),
                    "price_text": str(
                        self.cleaned_data.get("price_text") or ""
                    ).strip(),
                    "is_active": True,
                }
            ]

        service_areas = list(self.cleaned_data.get("service_areas") or [])
        if not service_areas and municipality is not None and mode:
            service_areas = [{"municipality_id": str(municipality.pk), "mode": mode}]

        languages = list(self.cleaned_data.get("languages") or [])
        if not languages and language is not None:
            languages = [{"language_id": str(language.pk), "declared": True}]

        contacts = list(self.cleaned_data.get("contacts") or [])
        if not contacts and contact_kind and contact_value:
            contacts = [
                {
                    "kind": contact_kind,
                    "value": contact_value,
                    "label": "",
                    "is_public": True,
                    "sort_order": 0,
                }
            ]

        return {
            "contacts": contacts,
            "services": services,
            "service_areas": service_areas,
            "languages": languages,
        }

    def cleaned_payload(self) -> dict[str, Any]:
        if not self.is_valid():
            raise ValueError("form must be valid before reading payload")
        return {
            "provider_type": self.cleaned_data["provider_type"],
            "legal_name": self.cleaned_data["legal_name"].strip(),
            "display_name": self.cleaned_data["display_name"].strip(),
            "y_tunnus": self.cleaned_data["y_tunnus"].strip(),
            **self._friendly_structured_payload(),
        }
