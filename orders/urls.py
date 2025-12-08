from django.urls import path
from .views import OrderCreateView, OrderListView, OrderDetailView, OrderPaymentView, PaymentSuccessView, PaymentCancelView

app_name = "orders"

urlpatterns = [
    path("create/", OrderCreateView.as_view(), name="order_create"),
    path("my-orders/", OrderListView.as_view(), name="order_list"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order_detail"),
    path("<int:pk>/pay/", OrderPaymentView.as_view(), name="order_pay"),
    path("payment/success/<int:pk>/", PaymentSuccessView.as_view(), name="payment_success"),
    path("payment/cancel/<int:pk>/", PaymentCancelView.as_view(), name="payment_cancel"),
    
]
