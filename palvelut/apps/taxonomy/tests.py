from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from .models import Country, Municipality, Region


class GeographyTaxonomyTests(TestCase):
    def setUp(self) -> None:
        self.finland = Country.objects.create(code="FI", name="Finland")
        self.region = Region.objects.create(
            country=self.finland,
            code="07",
            name="Central Ostrobothnia",
        )

    def test_database_generates_uuidv7_primary_keys(self) -> None:
        municipality = Municipality.objects.create(
            region=self.region,
            code="217",
            name="Kannus",
        )

        self.assertEqual(self.finland.id.version, 7)
        self.assertEqual(self.region.id.version, 7)
        self.assertEqual(municipality.id.version, 7)

    def test_country_code_is_iso_alpha2_shape(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            Country.objects.create(code="fi", name="Invalid")

    def test_region_code_is_unique_within_country(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            Region.objects.create(
                country=self.finland,
                code=self.region.code,
                name="Duplicate",
            )

    def test_municipality_code_is_unique_within_region(self) -> None:
        Municipality.objects.create(region=self.region, code="217", name="Kannus")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Municipality.objects.create(
                region=self.region,
                code="217",
                name="Duplicate",
            )

    def test_parent_rows_are_protected_from_deletion(self) -> None:
        municipality = Municipality.objects.create(
            region=self.region,
            code="217",
            name="Kannus",
        )

        with self.assertRaises(ProtectedError):
            self.region.delete()
        with self.assertRaises(ProtectedError):
            self.finland.delete()

        municipality.delete()
        self.region.delete()
        self.finland.delete()
