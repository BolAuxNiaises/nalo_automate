from django.core.management.base import BaseCommand

from ice_cream.models import Flavor


class Command(BaseCommand):
    """
    Management command to reset all flavor stocks to full capacity
    """

    help = "Reset all flavor stocks to 40 scoops"

    def add_arguments(self, parser):
        """Add command arguments"""
        parser.add_argument(
            "--confirm", action="store_true", help="Confirm the reset operation"
        )

    def handle(self, *args, **options):
        """Execute the command"""
        if not options["confirm"]:
            self.stdout.write(
                self.style.WARNING(
                    "This will reset ALL flavor stocks to 40 scoops.\n"
                    "Use --confirm flag to proceed."
                )
            )
            return

        flavors = Flavor.objects.all()

        if not flavors.exists():
            self.stdout.write(
                self.style.ERROR(
                    'No flavors found. Run "python manage.py init_flavors" first.'
                )
            )
            return

        self.stdout.write("Resetting all flavor stocks...")

        for flavor in flavors:
            old_stock = flavor.stock
            flavor.refill_pot()
            self.stdout.write(
                f"  ✓ {flavor.get_name_display()}: {old_stock} → 40 scoops"
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(f"Successfully reset {flavors.count()} flavors!")
        )
