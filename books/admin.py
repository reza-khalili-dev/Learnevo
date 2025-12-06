from django.contrib import admin
from .models import Book, BookCategory

@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'book_count', 'created_at')
    search_fields = ('name',)
    
    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = 'Number of Books'

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'book_type', 'price', 'stock', 'status', 'category')
    list_filter = ('book_type', 'status', 'category')
    search_fields = ('title', 'author', 'description')
    list_editable = ('price', 'stock', 'status')