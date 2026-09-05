from __future__ import annotations

from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from palvelut.apps.providers.models import Provider

from .adapters import RegistryLookupResult, RegistryOutcome
from .models import VerificationCheck
from .registry import (
    REGISTRY_CHECK_TYPES,
    RegistryCheckType,
    get_registry_check_type,
)
from .services import run_registry_check


class FakeBusinessIdentityAdapter:
    def lookup_business_id(self, business_id: str) -> RegistryLookupResult:
        return RegistryLookupResult(
            outcome=RegistryOutcome.FOUND,
            business_id=business_id,
            source_url="https://example.invalid/registry",
            fetched_at=datetime.now(timezone.utc),
            attempts=1,
            status_code=200,
            source_snapshot={"businessId": business_id},
        )


class RegistryCheckTypeTests(TestCase):
    def test_current_business_identity_check_is_enabled_and_extensible(self) -> None:
        definition = get_registry_check_type("business_identity")
        self.assertTrue(definition.enabled)
        self.assertFalse(definition.regulated_category)
        self.assertEqual(definition.subject_field, "y_tunnus")
        self.assertEqual(definition.lookup_method, "lookup_business_id")
        self.assertIsNotNone(definition.adapter_factory)

    def test_regulated_professional_right_check_is_registered_but_disabled(
        self,
    ) -> None:
        definition = REGISTRY_CHECK_TYPES["professional_right"]
        self.assertTrue(definition.regulated_category)
        self.assertFalse(definition.enabled)
        self.assertIsNone(definition.legal_source_review)
        with self.assertRaisesMessage(ValidationError, "pending legal/source review"):
            get_registry_check_type("professional_right")

    def test_regulated_type_cannot_be_enabled_without_recorded_review(self) -> None:
        unsafe = RegistryCheckType(
            kind="regulated_example",
            source_name="Example official source",
            subject_field="external_id",
            lookup_method="lookup",
            regulated_category=True,
            enabled=True,
            legal_source_review=None,
            adapter_factory=lambda: object(),
        )
        with self.assertRaisesMessage(RuntimeError, "legal/source review"):
            unsafe.validate_configuration()

    def test_unknown_kind_is_rejected(self) -> None:
        with self.assertRaisesMessage(ValidationError, "Unsupported verification kind"):
            get_registry_check_type("unknown_kind")


class GenericRegistryServiceTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="registry-staff",
            is_staff=True,
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Registry Example Oy",
            display_name="Registry Example",
            y_tunnus="0112038-9",
        )

    def test_enabled_type_runs_through_generic_registry_contract(self) -> None:
        check = run_registry_check(
            provider_id=self.provider.pk,
            actor=self.staff,
            kind="business_identity",
            adapter=FakeBusinessIdentityAdapter(),
        )
        self.assertEqual(check.status, VerificationCheck.Status.VERIFIED)
        self.assertEqual(check.kind, "business_identity")
        self.assertEqual(
            check.evidence_metadata["verification_kind"],
            "business_identity",
        )
        self.assertIn("registry_source", check.evidence_metadata)
        event = check.events.get()
        self.assertEqual(event.metadata["verification_kind"], "business_identity")

    def test_disabled_regulated_type_cannot_run_or_create_a_check(self) -> None:
        with self.assertRaisesMessage(ValidationError, "pending legal/source review"):
            run_registry_check(
                provider_id=self.provider.pk,
                actor=self.staff,
                kind="professional_right",
                adapter=object(),
            )
        self.assertFalse(
            VerificationCheck.objects.filter(
                provider=self.provider,
                kind="professional_right",
            ).exists()
        )
