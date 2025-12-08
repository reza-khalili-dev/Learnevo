from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from uuid import uuid4
from .models import Order, OrderItem
from books.models import Book


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.role in ["manager", "employee"]:
            return Order.objects.all().order_by("-created_at")
        return Order.objects.filter(user=self.request.user).order_by("-created_at")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_staff'] = self.request.user.role in ["manager", "employee"]
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        if self.request.user.role in ["manager", "employee"]:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    template_name = "orders/order_form.html"
    fields = [] 
    success_url = reverse_lazy("orders:order_list")

    def post(self, request, *args, **kwargs):
        book_id = request.POST.get("book_id")
        quantity = int(request.POST.get("quantity", 1))  
        book = get_object_or_404(Book, id=book_id)
        
        if book.is_physical and book.stock < quantity:
            messages.error(request, f"Only {book.stock} items available for '{book.title}'.")
            return redirect("books:book_detail", pk=book_id)
        
        order = Order.objects.create(
            user=request.user, 
            status="pending"
        )
        
        OrderItem.objects.create(
            order=order,
            book=book,
            quantity=quantity,
            unit_price=book.price
        )

        order.update_total()
        
        if book.is_physical:
            book.stock -= quantity
            book.save()
        
        messages.success(request, f"Your order for '{book.title}' has been placed successfully.")
        
        return redirect("orders:order_detail", pk=order.pk)


class OrderPaymentView(LoginRequiredMixin, UserPassesTestMixin, View):
    
    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        return render(request, "orders/payment_form.html", {"order": order})

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        
        if order.status == "paid":
            messages.warning(request, f"Order #{order.id} is already paid.")
            return redirect("orders:order_detail", pk=order.pk)
            
        transaction_id = str(uuid4())  
        order.status = "paid"
        order.transaction_id = transaction_id
        order.save(update_fields=["status", "transaction_id", "updated_at"])

        messages.success(request, f"Payment successful for Order #{order.id}. Transaction ID: {transaction_id}")

        return redirect("orders:payment_success", pk=order.pk)


class PaymentSuccessView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/payment_success.html"
    context_object_name = "order"

    def get_queryset(self):
        if self.request.user.role in ["manager", "employee"]:
            return Order.objects.filter(status="paid")
        return Order.objects.filter(user=self.request.user, status="paid")


class PaymentCancelView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/payment_cancel.html"
    context_object_name = "order"

    def get_queryset(self):
        if self.request.user.role in ["manager", "employee"]:
            return Order.objects.filter(status="pending")
        return Order.objects.filter(user=self.request.user, status="pending")


class OrderUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Order
    template_name = "orders/order_form.html"
    fields = ["status"]
    success_url = reverse_lazy("orders:order_list")

    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def form_valid(self, form):
        messages.success(self.request, f"Order #{self.object.id} updated successfully.")
        return super().form_valid(form)


class OrderDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Order
    template_name = "orders/order_confirm_delete.html"
    success_url = reverse_lazy("orders:order_list")

    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def delete(self, request, *args, **kwargs):
        order = self.get_object()
        

        for item in order.items.all():
            if item.book.is_physical:
                item.book.stock += item.quantity
                item.book.save()
        
        messages.success(request, f"Order #{order.id} deleted successfully. Stock restored.")
        return super().delete(request, *args, **kwargs)