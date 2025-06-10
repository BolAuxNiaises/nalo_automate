import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Flavor, Order, OrderItem


def index_view(request):
    """Homepage with navigation to main functions"""
    return render(request, "ice_cream/index.html")


def order_page_view(request):
    """Order creation page"""
    return render(request, "ice_cream/order.html")


def retrieve_order_page_view(request):
    """Order retrieval page"""
    return render(request, "ice_cream/retrieve.html")


def admin_dashboard_view(request):
    """Admin dashboard - revenue and fill rates"""
    flavors = Flavor.objects.all()
    recent_orders = Order.objects.order_by("-created_at")[:10]

    # Calculate statistics
    total_revenue = sum(order.total_price for order in Order.objects.all())
    total_orders = Order.objects.count()
    empty_pots_count = flavors.filter(stock=0).count()

    context = {
        "flavors": flavors,
        "recent_orders": recent_orders,
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "empty_pots_count": empty_pots_count,
    }
    return render(request, "ice_cream/admin.html", context)


# === API ENDPOINTS ===


@swagger_auto_schema(
    method="get",
    operation_description="Get all flavors with their stock information",
    responses={200: "List of flavors with stock levels"},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_flavors_api(request):
    """API: Get all available flavors with stock information"""
    flavors = Flavor.objects.all()
    flavors_data = []

    for flavor in flavors:
        flavors_data.append(
            {
                "id": flavor.id,
                "name": flavor.name,
                "display_name": flavor.get_name_display(),
                "stock": flavor.stock,
                "is_empty": flavor.is_empty,
                "fill_rate": flavor.fill_rate,
            }
        )

    return Response(
        {"success": True, "flavors": flavors_data, "total_flavors": len(flavors_data)}
    )


@swagger_auto_schema(
    method="post",
    operation_description="Create a new ice cream order",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["items"],
        properties={
            "items": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "flavor_id": openapi.Schema(
                            type=openapi.TYPE_INTEGER, description="Flavor ID"
                        ),
                        "quantity": openapi.Schema(
                            type=openapi.TYPE_INTEGER, description="Number of scoops"
                        ),
                    },
                ),
            )
        },
        example={
            "items": [{"flavor_id": 1, "quantity": 3}, {"flavor_id": 2, "quantity": 2}]
        },
    ),
    responses={
        200: "Order created successfully",
        400: "Validation error or insufficient stock",
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def create_order_api(request):
    """API: Create a new ice cream order"""
    try:
        order_items = request.data.get("items", [])

        if not order_items:
            return Response(
                {"error": "Aucun article dans la commande"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            total_price = 0
            items_to_create = []

            for item in order_items:
                flavor_id = item.get("flavor_id")
                quantity = item.get("quantity", 0)

                if quantity <= 0:
                    return Response(
                        {"error": "Quantité invalide"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                try:
                    flavor = Flavor.objects.select_for_update().get(id=flavor_id)
                except Flavor.DoesNotExist:
                    return Response(
                        {"error": f"Parfum inexistant: {flavor_id}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if flavor.stock < quantity:
                    return Response(
                        {
                            "error": f"Stock insuffisant pour {flavor.get_name_display()}. Stock disponible: {flavor.stock}"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                items_to_create.append(
                    {"flavor": flavor, "quantity": quantity, "price": quantity * 2}
                )
                total_price += quantity * 2

            # Create order
            order = Order.objects.create(total_price=total_price)

            # Create items and update stock
            for item_data in items_to_create:
                OrderItem.objects.create(
                    order=order,
                    flavor=item_data["flavor"],
                    quantity=item_data["quantity"],
                )

                # Update stock
                flavor = item_data["flavor"]
                flavor.consume_scoops(item_data["quantity"])

                # Check if pot is empty and send notification
                if flavor.is_empty:
                    _send_empty_pot_notification(flavor)

            return Response(
                {
                    "success": True,
                    "order_code": order.order_code,
                    "total_price": float(order.total_price),
                    "total_scoops": order.total_scoops,
                    "message": f"Commande créée avec succès!",
                }
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method="get",
    operation_description="Retrieve an order by its unique code",
    responses={200: "Order found", 404: "Order not found"},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_order_api(request, order_code):
    """API: Retrieve an order by its unique code"""
    try:
        order = Order.objects.get(order_code=order_code.upper())
        order_items = []

        for item in order.orderitem_set.all():
            order_items.append(
                {
                    "flavor": item.flavor.get_name_display(),
                    "flavor_code": item.flavor.name,
                    "quantity": item.quantity,
                    "price": float(item.item_price),
                }
            )

        return Response(
            {
                "success": True,
                "order": {
                    "code": order.order_code,
                    "total_price": float(order.total_price),
                    "total_scoops": order.total_scoops,
                    "created_at": order.created_at.strftime("%d/%m/%Y %H:%M"),
                    "items": order_items,
                },
            }
        )
    except Order.DoesNotExist:
        return Response(
            {"error": "Commande non trouvée"}, status=status.HTTP_404_NOT_FOUND
        )


@swagger_auto_schema(
    method="post",
    operation_description="Refill an ice cream pot to 40 scoops",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["flavor_id"],
        properties={
            "flavor_id": openapi.Schema(
                type=openapi.TYPE_INTEGER, description="Flavor ID to refill"
            )
        },
        example={"flavor_id": 1},
    ),
    responses={200: "Pot refilled successfully", 404: "Flavor not found"},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def refill_pot_api(request):
    """API: Refill an ice cream pot + send admin email (print simulation)"""
    try:
        flavor_id = request.data.get("flavor_id")

        flavor = Flavor.objects.get(id=flavor_id)
        old_stock = flavor.stock
        flavor.refill_pot()

        # Email notification (simulated by print)
        _send_refill_notification(flavor, old_stock)

        return Response(
            {
                "success": True,
                "message": f"Pot de {flavor.get_name_display()} rempli à 40 boules",
                "old_stock": old_stock,
                "new_stock": flavor.stock,
            }
        )
    except Flavor.DoesNotExist:
        return Response(
            {"error": "Parfum non trouvé"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _send_empty_pot_notification(flavor):
    """
    Send notification when a pot becomes empty
    (Simulated by print for testing)
    """
    print(f"🚨 EMPTY STOCK ALERT!")
    print(f"📧 Automatic email sent to administrator:")
    print(f"   Subject: Stock depleted - {flavor.get_name_display()}")
    print(f"   Message: The {flavor.get_name_display()} pot is now empty.")
    print(f"   Action required: Immediate restocking needed.")
    print(f"   Timestamp: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 50)


def _send_refill_notification(flavor, old_stock):
    """
    Send notification when a pot is refilled
    (Simulated by print for testing)
    """
    print(f"✅ POT REFILL COMPLETED")
    print(f"📧 Confirmation email sent to administrator:")
    print(f"   Subject: Pot refilled - {flavor.get_name_display()}")
    print(f"   Message: The {flavor.get_name_display()} pot has been refilled.")
    print(f"   Details: {old_stock} → 40 scoops (+{40 - old_stock} scoops)")
    print(f"   Timestamp: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 50)
