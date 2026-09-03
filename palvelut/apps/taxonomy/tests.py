from django.apps import apps
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from .models import (
    Category,
    CategoryLabel,
    CategorySynonym,
    Country,
    Municipality,
    Region,
    UuidV7Model,
)


class GeographyTaxonomyTests(TestCase):
    def setUp(self) -> None:
        self.finland = Country.objects.get(code="FI")
        self.region = self.finland.regions.get(code="16")

    def test_database_generates_uuidv7_primary_keys(self) -> None:
        municipality = Municipality.objects.create(
            region=self.region,
            code="998",
            name="Test municipality",
        )

        self.assertEqual(self.finland.id.version, 7)
        self.assertEqual(self.region.id.version, 7)
        self.assertEqual(municipality.id.version, 7)

    def test_uuidv7_models_use_native_postgresql_database_defaults(self) -> None:
        self.assertGreaterEqual(connection.pg_version, 180000)

        uuid_models = [
            model
            for model in apps.get_models()
            if issubclass(model, UuidV7Model) and not model._meta.abstract
        ]
        self.assertTrue(uuid_models)

        with connection.cursor() as cursor:
            for model in uuid_models:
                cursor.execute(
                    """
                    SELECT pg_get_expr(attr_default.adbin, attr_default.adrelid)
                    FROM pg_attrdef AS attr_default
                    JOIN pg_attribute AS attribute
                      ON attribute.attrelid = attr_default.adrelid
                     AND attribute.attnum = attr_default.adnum
                    WHERE attr_default.adrelid = %s::regclass
                      AND attribute.attname = 'id'
                    """,
                    [model._meta.db_table],
                )
                row = cursor.fetchone()
                self.assertIsNotNone(row, model._meta.label)
                self.assertEqual(row[0], "uuidv7()", model._meta.label)

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
        with self.assertRaises(IntegrityError), transaction.atomic():
            Municipality.objects.create(
                region=self.region,
                code="217",
                name="Duplicate Kannus",
            )

    def test_parent_rows_are_protected_from_deletion(self) -> None:
        with self.assertRaises(ProtectedError):
            self.region.delete()
        with self.assertRaises(ProtectedError):
            self.finland.delete()


class SeededTaxonomyTests(TestCase):
    launch_slugs = {
        "accounting",
        "legal",
        "car-repair",
        "renovation",
        "electrical",
        "plumbing",
        "psychology",
        "massage-physiotherapy",
    }

    def test_all_2026_finnish_municipalities_are_seeded(self) -> None:
        finland = Country.objects.get(code="FI")
        municipalities = Municipality.objects.filter(region__country=finland)

        self.assertEqual(finland.regions.count(), 19)
        self.assertEqual(municipalities.count(), 308)
        self.assertEqual(
            dict(
                municipalities.filter(code__in=("049", "091", "092")).values_list(
                    "code", "name"
                )
            ),
            {"049": "Espoo", "091": "Helsinki", "092": "Vantaa"},
        )
        self.assertFalse(
            municipalities.filter(code__in=("049", "091", "092"))
            .exclude(region__code="01")
            .exists()
        )

    def test_launch_categories_have_ru_fi_en_labels_and_synonyms(self) -> None:
        categories = Category.objects.filter(slug__in=self.launch_slugs)
        self.assertEqual(categories.count(), 8)

        for category in categories:
            self.assertEqual(
                set(category.labels.values_list("locale", flat=True)),
                {"ru", "fi", "en"},
                category.slug,
            )
            for locale in ("ru", "fi", "en"):
                self.assertGreaterEqual(
                    category.synonyms.filter(locale=locale).count(),
                    2,
                    f"{category.slug}/{locale}",
                )

        accounting = Category.objects.get(slug="accounting")
        self.assertEqual(
            accounting.labels.get(locale="ru").label,
            "Бухгалтерия",
        )
        self.assertTrue(
            accounting.synonyms.filter(locale="fi", value="kirjanpitäjä").exists()
        )

    def test_category_terms_reject_unsupported_locale_and_duplicates(self) -> None:
        category = Category.objects.get(slug="accounting")

        with self.assertRaises(IntegrityError), transaction.atomic():
            CategoryLabel.objects.create(
                category=category, locale="sv", label="Bokföring"
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            CategoryLabel.objects.create(
                category=category,
                locale="en",
                label="Duplicate accounting",
            )

        synonym = category.synonyms.filter(locale="en").first()
        self.assertIsNotNone(synonym)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CategorySynonym.objects.create(
                category=category,
                locale=synonym.locale,
                value=synonym.value,
            )
