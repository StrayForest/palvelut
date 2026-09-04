from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ProviderMigrationRoundTripTests(TransactionTestCase):
    migrate_from = ("providers", "0003_provider_claim_state")
    migrate_to = ("providers", "0004_membership_requires_approved_claim")
    trigger_name = "providers_membership_requires_approved_claim_trigger"
    function_name = "providers_membership_requires_approved_claim"

    def setUp(self) -> None:
        if connection.vendor != "postgresql":
            self.skipTest("P1 migration round-trip is verified against PostgreSQL")

    def tearDown(self) -> None:
        if connection.vendor == "postgresql":
            MigrationExecutor(connection).migrate([self.migrate_to])
        super().tearDown()

    def trigger_exists(self) -> bool:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_trigger
                    WHERE tgname = %s
                      AND NOT tgisinternal
                )
                """,
                [self.trigger_name],
            )
            row = cursor.fetchone()
        return bool(row and row[0])

    def function_exists(self) -> bool:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT to_regprocedure(%s) IS NOT NULL",
                [f"{self.function_name}()"],
            )
            row = cursor.fetchone()
        return bool(row and row[0])

    def test_membership_claim_trigger_migrates_forward_and_backward(self) -> None:
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        self.assertFalse(self.trigger_exists())
        self.assertFalse(self.function_exists())

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        self.assertTrue(self.trigger_exists())
        self.assertTrue(self.function_exists())

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        self.assertFalse(self.trigger_exists())
        self.assertFalse(self.function_exists())
