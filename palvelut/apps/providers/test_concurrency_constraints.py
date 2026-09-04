from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.contrib.auth import get_user_model
from django.db import IntegrityError, close_old_connections, transaction
from django.test import TransactionTestCase

from .models import Provider, ProviderMembership


class ProviderConcurrencyConstraintTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self) -> None:
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Concurrent Oy",
            display_name="Concurrent",
            claim_status=Provider.ClaimStatus.APPROVED,
            claim_evidence={"kind": "staff_review", "reference": "concurrency"},
        )
        self.first_user = get_user_model().objects.create_user(username="owner-a")
        self.second_user = get_user_model().objects.create_user(username="owner-b")

    def run_concurrently(self, first, second):  # type: ignore[no-untyped-def]
        barrier = Barrier(2)

        def guarded(callback):  # type: ignore[no-untyped-def]
            close_old_connections()
            try:
                barrier.wait(timeout=5)
                try:
                    with transaction.atomic():
                        callback()
                except IntegrityError:
                    return "integrity-error"
                return "created"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(guarded, callback) for callback in (first, second)]
            return sorted(future.result(timeout=10) for future in futures)

    def test_nonblank_y_tunnus_remains_unique_under_concurrent_insert(self) -> None:
        y_tunnus = "7654321-0"

        def create_provider(name: str) -> None:
            Provider.objects.create(
                provider_type=Provider.Type.BUSINESS,
                legal_name=name,
                display_name=name,
                y_tunnus=y_tunnus,
            )

        results = self.run_concurrently(
            lambda: create_provider("First Oy"),
            lambda: create_provider("Second Oy"),
        )

        self.assertEqual(results, ["created", "integrity-error"])
        self.assertEqual(Provider.objects.filter(y_tunnus=y_tunnus).count(), 1)

    def test_provider_keeps_one_active_owner_under_concurrent_insert(self) -> None:
        def create_owner(user) -> None:  # type: ignore[no-untyped-def]
            ProviderMembership.objects.create(
                provider=self.provider,
                account=user,
                role=ProviderMembership.Role.OWNER,
                is_active=True,
            )

        results = self.run_concurrently(
            lambda: create_owner(self.first_user),
            lambda: create_owner(self.second_user),
        )

        self.assertEqual(results, ["created", "integrity-error"])
        self.assertEqual(
            ProviderMembership.objects.filter(
                provider=self.provider,
                role=ProviderMembership.Role.OWNER,
                is_active=True,
            ).count(),
            1,
        )
