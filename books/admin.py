from django.contrib import admin
from .models import Book

# Register your models here.

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "book_type", "price", "stock", "is_physical", "created_at")
    search_fields = ("title", "author")
    list_filter = ("book_type", "shipping_available", "created_at")
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "author", "description", "price")
        }),
        ("Book Details", {
            "fields": ("book_type", "file", "external_link", "stock", "shipping_available")
        }),
        ("Uploader & Time", {
            "fields": ("uploaded_by", "created_at", "updated_at")
        }),
    )

    readonly_fields = ("created_at", "updated_at")
