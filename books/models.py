from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import os


class BookCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Book Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Book(models.Model):
    BOOK_TYPE_CHOICES = [
        ("digital", "Digital"),
        ("physical", "Physical"),
        ("both", "Digital & Physical"),
    ]
    
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("out_of_stock", "Out of Stock"),
    ]
    
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    book_type = models.CharField(max_length=10, choices=BOOK_TYPE_CHOICES, default="digital")
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='books/covers/', blank=True, null=True, help_text="Cover image of the book")
    file = models.FileField(upload_to='books/files/', blank=True, null=True)
    external_link = models.URLField(blank=True, null=True)
    stock = models.PositiveIntegerField(default=0, help_text="Number of physical books in stock")
    min_stock_alert = models.PositiveIntegerField(default=5, help_text="Alert when stock goes below this number")
    shipping_available = models.BooleanField(default=True, help_text="Is mailing enabled?")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="active")
    category = models.ForeignKey(BookCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="books")
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_books")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['author']),
            models.Index(fields=['status', 'book_type']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
    @property
    def is_digital(self):
        return self.book_type in ["digital", "both"]

    @property
    def is_physical(self):
        return self.book_type in ["physical", "both"]
    
    @property
    def stock_status(self):
        if self.stock == 0:
            return "danger"  
        elif self.stock < self.min_stock_alert:
            return "warning"  
        else:
            return "success"  
    
    @property
    def total_value(self):
        """ارزش کل موجودی این کتاب"""
        return self.price * self.stock
    
    def save(self, *args, **kwargs):

        if self.is_physical and self.stock == 0:
            self.status = "out_of_stock"
        elif self.status == "out_of_stock" and self.stock > 0:
            self.status = "active"
        super().save(*args, **kwargs)