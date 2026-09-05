from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision, ProviderSlug

from .models import VerificationCheck
from .presentation import public_verification_facts
from .services import recheck_expiry_queue


@override_settings(ALLOWED_HOSTS=["testserver"])
class PublicTrustTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.staff = get_user_model().objects.create_user(
            username="trust-reviewer",
            is_staff=True,
        )
        cls.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.PUBLISHED,
            claim_status=Provider.ClaimStatus.APPROVED,
            claim_evidence={"source": "test"},
            legal_name="Trust Example Oy",
            display_name="Trust Example",
            y_tunnus="1234567-1",
        )
        revision = ProfileRevision.objects.create(
            provider=cls.provider,
            status=ProfileRevision.Status.APPROVED,
            payload={"display_name": "Trust Example"},
            created_by=cls.staff,
            reviewed_at=timezone.now(),
        )
        ProviderReadDocument.objects.create(
            provider=cls.provider,
            source_revision=revision,
            document=revision.payload,
        )
        ProviderSlug.objects.create(
            provider=cls.provider,
            slug="trust-example",
            is_current=True,
        )

    def _check(
        self,
        *,
        status: str = "verified",
        checked_at=None,
        expires_at=None,
    ) -> VerificationCheck:
        check = VerificationCheck.objects.create(
            provider=self.provider,
            kind="business_identity",
            status=status,
            source_url="https://avoindata.prh.fi/",
            checked_by=self.staff,
            expires_at=expires_at,
        )
        if checked_at is not None:
            VerificationCheck.objects.filter(pk=check.pk).update(checked_at=checked_at)
            check.refresh_from_db()
        return check

    def test_public_fact_names_exact_fact_source_and_check_date(self) -> None:
        checked_at = timezone.now() - timedelta(days=2)
        self._check(
            checked_at=checked_at,
            expires_at=timezone.now() + timedelta(days=30),
        )

        facts = public_verification_facts(self.provider)

        self.assertEqual(len(facts), 1)
        self.assertEqual(
            facts[0].label,
            "Y-tunnus found in PRH YTJ Open Data API v3 · checked "
            f"{timezone.localtime(checked_at).date().isoformat()}",
        )
        self.assertNotIn("Verified professional", facts[0].label)

    def test_expired_fact_is_hidden_and_enters_recheck_queue(self) -> None:
        now = timezone.now()
        expired = self._check(
            checked_at=now - timedelta(days=10),
            expires_at=now - timedelta(seconds=1),
        )

        self.assertEqual(public_verification_facts(self.provider, at=now), [])
        self.assertEqual(list(recheck_expiry_queue(at=now)), [expired])

    def test_newer_check_removes_old_expired_fact_from_recheck_queue(self) -> None:
        now = timezone.now()
        self._check(
            checked_at=now - timedelta(days=10),
            expires_at=now - timedelta(days=1),
        )
        self._check(
            status="pending",
            checked_at=now - timedelta(hours=1),
        )

        self.assertEqual(list(recheck_expiry_queue(at=now)), [])

    def test_profile_and_trust_page_explain_fact_only_semantics(self) -> None:
        checked_at = timezone.now() - timedelta(days=1)
        self._check(
            checked_at=checked_at,
            expires_at=timezone.now() + timedelta(days=30),
        )

        profile = self.client.get("/palvelut/en/professionals/trust-example/")
        self.assertEqual(profile.status_code, 200)
        self.assertContains(profile, "Y-tunnus found in PRH YTJ Open Data API v3")
        self.assertContains(profile, "How verification works")
        self.assertNotContains(profile, "Verified professional")

        trust = self.client.get("/palvelut/en/trust/")
        self.assertEqual(trust.status_code, 200)
        self.assertContains(trust, "fact checked, official source and check date")
        self.assertContains(trust, "not a rating of service quality")
        self.assertContains(trust, "does not prove any licence")
