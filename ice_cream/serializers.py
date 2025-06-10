from rest_framework import serializers

from .models import Flavor, Order, OrderItem


class FlavorSerializer(serializers.ModelSerializer):
    """
    Serializer for ice cream flavors
    """

    display_name = serializers.CharField(source="get_name_display", read_only=True)
    is_empty = serializers.BooleanField(read_only=True)
    fill_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = Flavor
        fields = ["id", "name", "display_name", "stock", "is_empty", "fill_rate"]


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for order items
    """

    flavor_name = serializers.CharField(
        source="flavor.get_name_display", read_only=True
    )
    flavor_code = serializers.CharField(source="flavor.name", read_only=True)
    item_price = serializers.FloatField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["flavor_name", "flavor_code", "quantity", "item_price"]


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed order information
    """

    items = OrderItemSerializer(source="orderitem_set", many=True, read_only=True)
    total_scoops = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = ["order_code", "total_price", "total_scoops", "created_at", "items"]


class OrderItemCreateSerializer(serializers.Serializer):
    """
    Serializer for creating order items
    """

    flavor_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating new orders
    """

    items = OrderItemCreateSerializer(many=True)

    def validate_items(self, value):
        """
        Validate that items list is not empty
        """
        if not value:
            raise serializers.ValidationError("At least one item is required")
        return value


class RefillPotSerializer(serializers.Serializer):
    """
    Serializer for pot refill requests
    """

    flavor_id = serializers.IntegerField()
