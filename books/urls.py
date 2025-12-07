from django.urls import path
from .views import (
    BookListView, BookDetailView, BookCreateView, 
    BookUpdateView, BookDeleteView, BookDashboardView,
    BookSearchView, QuickOrderCreateView, BookReturnView,
    CategoryListView, CategoryCreateView, CategoryUpdateView,
    CategoryDeleteView, CategoryBulkActionView
)
from django.views.decorators.csrf import csrf_exempt

app_name = "books"

urlpatterns = [
    # main urls
    path("", BookListView.as_view(), name="book_list"),
    path("dashboard/", BookDashboardView.as_view(), name="dashboard"),
    path("search/", BookSearchView.as_view(), name="book_search"),
    path("quick-order/", csrf_exempt(QuickOrderCreateView.as_view()), name="quick_order"),
    path("return-book/", csrf_exempt(BookReturnView.as_view()), name="return_book"),
    path("<int:pk>/", BookDetailView.as_view(), name="book_detail"),
    path("add/", BookCreateView.as_view(), name="book_add"),
    path("<int:pk>/edit/", BookUpdateView.as_view(), name="book_edit"),
    path("<int:pk>/delete/", BookDeleteView.as_view(), name="book_delete"),
    
    # Category management
    path("categories/", CategoryListView.as_view(), name="category_list"),
    path("categories/add/", CategoryCreateView.as_view(), name="category_add"),
    path("categories/<int:pk>/edit/", CategoryUpdateView.as_view(), name="category_edit"),
    path("categories/<int:pk>/delete/", CategoryDeleteView.as_view(), name="category_delete"),
    path("categories/bulk-action/", CategoryBulkActionView.as_view(), name="category_bulk_action"),
]