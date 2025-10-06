from decimal import Decimal
from django.db import models
from django.conf import settings

# Create your models here.

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="orders")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.email} - {self.status}"
    
    def calculate_total(self):
        total = Decimal("0.00")
        for item in self.items.all():
            total += item.unit_price * item.quantity
        return total
    
    def update_total(self):
        self.total = self.calculate_total()
        self.save(update_fields=["total", "updated_at"])


class OrderItem(models.Model):
    
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name="items")
    book = models.ForeignKey("books.Book",on_delete=models.PROTECT,related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def line_total(self):
        return self.unit_price * self.quantity
    
    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.book.price
        super().save(*args, **kwargs)
        self.order.update_total()
    
    def __str__(self):
        return f"{self.book.title} x{self.quantity} (Order #{self.order.id})"
        