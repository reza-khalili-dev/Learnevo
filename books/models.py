from django.db import models
from django.conf import settings


# Create your models here.


class Book(models.Model):
    BOOK_TYPE_CHOICES = [
        ("digital", "Digital"),
        ("physical", "Physical"),
        ("both", "Digital & Physical"),
    ]
    
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    book_type = models.CharField(max_length=10,choices=BOOK_TYPE_CHOICES,default="digital")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    file = models.FileField(upload_to='books/', blank=True, null=True)
    external_link = models.URLField(blank=True, null=True)
    stock = models.PositiveIntegerField(default=0, help_text="Number of physical books in stock")
    shipping_available = models.BooleanField(default=True, help_text="Is mailing enabled?")
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="uploaded_books")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.author}"
    
    @property
    def is_digital(self):
        return self.book_type in ["digital", "both"]

    @property
    def is_physical(self):
        return self.book_type in ["physical", "both"]