from django.urls import path
from .views import BookListView,BookDetailView,BookCreateView,BookUpdateView,BookDeleteView

app_name = "books"

urlpatterns = [
    path("", BookListView.as_view(), name="book_list"),
    path("<int:pk>/", BookDetailView.as_view(), name="book_detail"),
    path("add/", BookCreateView.as_view(), name="book_add"),
    path("<int:pk>/edit/", BookUpdateView.as_view(), name="book_edit"),
    path("<int:pk>/delete/", BookDeleteView.as_view(), name="book_delete"),
]

