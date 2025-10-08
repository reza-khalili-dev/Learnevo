# orders/urls.py
from django.urls import path
from .views import OrderCreateView, OrderListView, OrderDetailView

app_name = "orders"

urlpatterns = [
    path("create/", OrderCreateView.as_view(), name="order_create"),
    path("my-orders/", OrderListView.as_view(), name="order_list"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order_detail"),
]
