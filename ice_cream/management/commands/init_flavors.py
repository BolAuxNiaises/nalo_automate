from django.core.management.base import BaseCommand

from ice_cream.models import Flavor


class Command(BaseCommand):
    """
    Management command to initialize ice cream flavors
    """

    help = "Initialize ice cream flavors with default stock"

    def add_arguments(self, parser):
        """Add command arguments"""
        parser.add_argument(
            "--stock",
            type=int,
            default=40,
            help="Initial stock for each flavor (default: 40)",
        )
        parser.add_argument(
            "--force", action="store_true", help="Force update existing flavors"
        )

    def handle(self, *args, **options):
        """Execute the command"""
        initial_stock = options["stock"]
        force_update = options["force"]

        flavors_data = [
            ("chocolate_orange", "Chocolat Orange"),
            ("cherry", "Cerise"),
            ("pistachio", "Pistache"),
            ("vanilla", "Vanille"),
            ("raspberry", "Framboise"),
        ]

        created_count = 0
        updated_count = 0

        for flavor_code, flavor_display in flavors_data:
            flavor, created = Flavor.objects.get_or_create(
                name=flavor_code, defaults={"stock": initial_stock}
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Created flavor: {flavor_display} with {initial_stock} scoops"
                    )
                )
            elif force_update:
                flavor.stock = initial_stock
                flavor.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"↻ Updated flavor: {flavor_display} to {initial_stock} scoops"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"- Flavor already exists: {flavor_display} ({flavor.stock} scoops)"
                    )
                )

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Initialization complete!"))
        self.stdout.write(f"  - Created: {created_count} flavors")
        if force_update:
            self.stdout.write(f"  - Updated: {updated_count} flavors")
        self.stdout.write(f"  - Total flavors: {Flavor.objects.count()}")
