from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from palvelut.apps.providers.models import Provider
from palvelut.apps.providers.services import import_unclaimed_provider


class Command(BaseCommand):
    help = "Idempotently import one non-public provider by Y-tunnus."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--actor", required=True)
        parser.add_argument("--y-tunnus", required=True)
        parser.add_argument("--legal-name", required=True)
        parser.add_argument("--display-name", required=True)
        parser.add_argument(
            "--provider-type",
            choices=[choice for choice, _label in Provider.Type.choices],
            default=Provider.Type.BUSINESS,
        )

    def handle(self, *args, **options) -> None:
        user_model = get_user_model()
        try:
            actor = user_model.objects.get(username=options["actor"], is_staff=True)
        except user_model.DoesNotExist as exc:
            raise CommandError("Actor must be an existing staff user.") from exc

        provider = import_unclaimed_provider(
            actor=actor,
            data={
                "y_tunnus": options["y_tunnus"],
                "legal_name": options["legal_name"],
                "display_name": options["display_name"],
                "provider_type": options["provider_type"],
            },
        )
        self.stdout.write(str(provider.pk))
