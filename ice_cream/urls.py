from django.urls import path

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from . import views

# Swagger configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Nalo Ice Cream Automate API",
        default_version="v1",
        description="""
        API for the Nalo Ice Cream Automate system.
        
        Features:
        - Flavor and stock management
        - Order creation and retrieval
        - Pot refilling
        - Stock alerts
        
        Each scoop costs 2€, each pot contains 40 scoops maximum.
        """,
        contact=openapi.Contact(email="tech@nalo.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

app_name = "ice_cream"

urlpatterns = [
    # Web pages (URLs en anglais, interface en français)
    path("", views.index_view, name="index"),
    path(
        "order/", views.order_page_view, name="order"
    ),  # /order/ au lieu de /commander/
    path(
        "retrieve/", views.retrieve_order_page_view, name="retrieve"
    ),  # /retrieve/ au lieu de /recuperer/
    path("admin-dashboard/", views.admin_dashboard_view, name="admin_dashboard"),
    # API endpoints (URLs en anglais)
    path("api/flavors/", views.get_flavors_api, name="api_get_flavors"),
    path("api/orders/", views.create_order_api, name="api_create_order"),
    path("api/orders/<str:order_code>/", views.get_order_api, name="api_get_order"),
    path("api/refill-pot/", views.refill_pot_api, name="api_refill_pot"),
    # API Documentation
    path(
        "api/docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
    path("api/schema/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
]
