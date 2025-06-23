import random

from django.core.management.base import BaseCommand
from django.db import transaction

from ice_cream.models import Flavor, Order, OrderItem


class Command(BaseCommand):
    """
    Management command to generate sample orders for testing
    """

    help = "Generate sample orders for testing purposes"

    def add_arguments(self, parser):
        """Add command arguments"""
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of orders to generate (default: 10)",
        )
        parser.add_argument(
            "--max-items",
            type=int,
            default=3,
            help="Maximum items per order (default: 3)",
        )

    def handle(self, *args, **options):
        """Execute the command"""
        order_count = options["count"]
        max_items = options["max_items"]

        if not Flavor.objects.exists():
            self.stdout.write(
                self.style.ERROR(
                    'No flavors found. Run "python manage.py init_flavors" first.'
                )
            )
            return

        flavors = list(Flavor.objects.all())
        generated_orders = []

        self.stdout.write(f"Generating {order_count} sample orders...")

        with transaction.atomic():
            for i in range(order_count):
                # Random number of items per order (1 to max_items)
                num_items = random.randint(1, max_items)

                # Select random flavors
                selected_flavors = random.sample(flavors, num_items)

                total_price = 0
                order_items_data = []

                for flavor in selected_flavors:
                    # Random quantity (1 to 5 scoops)
                    quantity = random.randint(1, min(5, flavor.stock))

                    if quantity > 0:
                        order_items_data.append(
                            {"flavor": flavor, "quantity": quantity}
                        )
                        total_price += quantity * 2

                if order_items_data:
                    # Create order
                    order = Order.objects.create(total_price=total_price)

                    # Create order items
                    for item_data in order_items_data:
                        OrderItem.objects.create(
                            order=order,
                            flavor=item_data["flavor"],
                            quantity=item_data["quantity"],
                        )

                        # Update stock
                        flavor = item_data["flavor"]
                        flavor.consume_scoops(item_data["quantity"])

                    generated_orders.append(order)

                    self.stdout.write(
                        f"  ✓ Order {order.order_code}: {total_price}€ ({order.total_scoops} scoops)"
                    )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully generated {len(generated_orders)} orders!"
            )
        )

        # Show updated stock levels
        self.stdout.write("\nUpdated stock levels:")
        for flavor in Flavor.objects.all():
            status = "🔴" if flavor.is_empty else "🟡" if flavor.stock < 10 else "🟢"
            self.stdout.write(
                f"  {status} {flavor.get_name_display()}: {flavor.stock} scoops"
            )
