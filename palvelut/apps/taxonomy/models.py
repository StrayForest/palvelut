from django.db import models
from django.db.models import Q


class UuidV7Model(models.Model):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        db_default=models.Func(function="uuidv7"),
    )

    class Meta:
        abstract = True


class Country(UuidV7Model):
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ("code",)
        constraints = [
            models.CheckConstraint(
                condition=Q(code__regex=r"^[A-Z]{2}$"),
                name="taxonomy_country_code_iso_alpha2",
            )
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class Region(UuidV7Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="regions",
    )
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ("country_id", "code")
        constraints = [
            models.UniqueConstraint(
                fields=("country", "code"),
                name="taxonomy_region_country_code_unique",
            )
        ]

    def __str__(self) -> str:
        return f"{self.country.code}/{self.code} — {self.name}"


class Municipality(UuidV7Model):
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="municipalities",
    )
    code = models.CharField(max_length=16)
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ("region_id", "code")
        constraints = [
            models.UniqueConstraint(
                fields=("region", "code"),
                name="taxonomy_municipality_region_code_unique",
            )
        ]

    def __str__(self) -> str:
        return f"{self.region.country.code}/{self.region.code}/{self.code} — {self.name}"
