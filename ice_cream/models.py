# models.py
import random
import string
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Flavor(models.Model):
    """
    Ice cream flavor model with stock management
    """

    FLAVOR_CHOICES = [
        ("chocolate_orange", "Chocolat Orange"),
        ("cherry", "Cerise"),
        ("pistachio", "Pistache"),
        ("vanilla", "Vanille"),
        ("raspberry", "Framboise"),
    ]

    name = models.CharField(max_length=50, choices=FLAVOR_CHOICES, unique=True)
    stock = models.IntegerField(default=40, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.get_name_display()

    @property
    def is_empty(self):
        """Check if the pot is empty"""
        return self.stock == 0

    @property
    def fill_rate(self):
        """Calculate fill rate percentage"""
        return (self.stock / 40) * 100

    def refill_pot(self):
        """Refill the pot to 40 scoops"""
        self.stock = 40
        self.save()

    def consume_scoops(self, quantity):
        """
        Consume scoops from stock
        Returns True if successful, False if insufficient stock
        """
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False


class Order(models.Model):
    """
    Customer order with unique code generation
    """

    order_code = models.CharField(max_length=8, unique=True, editable=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.order_code:
            self.order_code = self._generate_unique_code()
        super().save(*args, **kwargs)

    def _generate_unique_code(self):
        """Generate a unique 8-character order code"""
        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Order.objects.filter(order_code=code).exists():
                return code

    @property
    def total_scoops(self):
        """Calculate total number of scoops in the order"""
        return sum(item.quantity for item in self.orderitem_set.all())

    def __str__(self):
        return f"Order {self.order_code} - {self.total_price}€"


class OrderItem(models.Model):
    """
    Individual item within an order
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    flavor = models.ForeignKey(Flavor, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.quantity} scoop(s) {self.flavor.get_name_display()}"

    @property
    def item_price(self):
        """Calculate price for this item (quantity * 2€)"""
        return self.quantity * 2


class AdminSettings(models.Model):
    """
    Admin configuration settings
    """

    admin_email = models.EmailField(default="admin@nalo.com")
    low_stock_threshold = models.IntegerField(default=5)

    class Meta:
        verbose_name = "Admin Configuration"
        verbose_name_plural = "Admin Configurations"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_default_settings(cls):
        """Get or create default admin settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
