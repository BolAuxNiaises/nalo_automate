from django.contrib import admin

from .models import AdminSettings, Flavor, Order, OrderItem


@admin.register(Flavor)
class FlavorAdmin(admin.ModelAdmin):
    """
    Admin interface for ice cream flavors
    """

    list_display = [
        "get_name_display",
        "stock",
        "fill_rate_display",
        "is_empty_display",
    ]
    list_filter = ["name"]
    actions = ["refill_selected_pots"]
    readonly_fields = ["fill_rate_display", "is_empty_display"]

    def fill_rate_display(self, obj):
        """Display fill rate as percentage"""
        return f"{obj.fill_rate:.1f}%"

    fill_rate_display.short_description = "Taux de remplissage"

    def is_empty_display(self, obj):
        """Display empty status with icon"""
        if obj.is_empty:
            return "🔴 Vide"
        elif obj.stock < 10:
            return "🟡 Faible"
        else:
            return "🟢 OK"

    is_empty_display.short_description = "Statut"

    def refill_selected_pots(self, request, queryset):
        """Admin action to refill selected pots"""
        count = queryset.count()
        for flavor in queryset:
            flavor.refill_pot()
        self.message_user(request, f"{count} pot(s) rempli(s) à 40 boules.")

    refill_selected_pots.short_description = "Remplir les pots sélectionnés"


class OrderItemInline(admin.TabularInline):
    """
    Inline admin for order items
    """

    model = OrderItem
    extra = 0
    readonly_fields = ["item_price_display"]

    def item_price_display(self, obj):
        """Display item price"""
        return f"{obj.item_price}€"

    item_price_display.short_description = "Prix"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin interface for orders
    """

    list_display = ["order_code", "total_price", "total_scoops_display", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["order_code"]
    readonly_fields = [
        "order_code",
        "total_price",
        "created_at",
        "total_scoops_display",
    ]
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"

    def total_scoops_display(self, obj):
        """Display total scoops count"""
        return f"{obj.total_scoops} boule(s)"

    total_scoops_display.short_description = "Total boules"

    def has_add_permission(self, request):
        """Prevent manual order creation in admin"""
        return False


@admin.register(AdminSettings)
class AdminSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for settings
    """

    list_display = ["admin_email", "low_stock_threshold"]
    fieldsets = (
        ("Configuration Email", {"fields": ("admin_email",)}),
        ("Seuils d'alerte", {"fields": ("low_stock_threshold",)}),
    )

    def has_add_permission(self, request):
        """Only allow one settings instance"""
        return not AdminSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent settings deletion"""
        return False


# Customize admin site headers
admin.site.site_header = "Administration Automate Nalo"
admin.site.site_title = "Nalo Admin"
admin.site.index_title = "Gestion de l'automate de glaces"
