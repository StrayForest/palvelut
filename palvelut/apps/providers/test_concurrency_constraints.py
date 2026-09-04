from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.contrib.auth import get_user_model
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.test import TransactionTestCase

from .models import Provider, ProviderMembership


class ProviderConcurrencyConstraintTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self) -> None:
        if connection.vendor != "postgresql":
            self.skipTest("P1 concurrency constraints are verified against PostgreSQL")

    def run_race(self, callbacks):  # type: ignore[no-untyped-def]
        barrier = Barrier(len(callbacks))

        def runner(callback):  # type: ignore[no-untyped-def]
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    with transaction.atomic():
                        callback()
                except IntegrityError:
                    return False
                return True
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=len(callbacks)) as executor:
            return list(executor.map(runner, callbacks))

    def test_duplicate_y_tunnus_race_commits_only_one_provider(self) -> None:
        y_tunnus = "7654321-0"

        def create_provider(name: str) -> None:
            Provider.objects.create(
                provider_type=Provider.Type.BUSINESS,
                legal_name=f"{name} Oy",
                display_name=name,
                y_tunnus=y_tunnus,
            )

        results = self.run_race(
            [
                lambda: create_provider("Concurrent A"),
                lambda: create_provider("Concurrent B"),
            ],
        )

        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(Provider.objects.filter(y_tunnus=y_tunnus).count(), 1)

    def test_active_owner_race_commits_only_one_membership(self) -> None:
        provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Concurrent Owner Oy",
            display_name="Concurrent Owner",
            claim_status=Provider.ClaimStatus.APPROVED,
            claim_evidence={"kind": "staff_review", "reference": "concurrency-test"},
        )
        first_user = get_user_model().objects.create_user(username="concurrent-owner-1")
        second_user = get_user_model().objects.create_user(username="concurrent-owner-2")

        def create_owner(user_id: int) -> None:
            ProviderMembership.objects.create(
                provider_id=provider.pk,
                account_id=user_id,
                role=ProviderMembership.Role.OWNER,
                is_active=True,
            )

        results = self.run_race(
            [
                lambda: create_owner(first_user.pk),
                lambda: create_owner(second_user.pk),
            ],
        )

        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(
            ProviderMembership.objects.filter(
                provider=provider,
                role=ProviderMembership.Role.OWNER,
                is_active=True,
            ).count(),
            1,
        )
