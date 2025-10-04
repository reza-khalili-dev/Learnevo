from django.urls import path
from .views import BookListView,BookDetailView,BookCreateView,BookUpdateView,BookDeleteView

app_name = "materials"

urlpatterns = [
    path("", BookListView.as_view(), name="book-list"),
    path("<int:pk>/", BookDetailView.as_view(), name="book-detail"),
    path("add/", BookCreateView.as_view(), name="book-add"),
    path("<int:pk>/edit/", BookUpdateView.as_view(), name="book-edit"),
    path("<int:pk>/delete/", BookDeleteView.as_view(), name="book-delete"),
]

