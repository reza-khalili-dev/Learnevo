from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import  ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Book


# Create your views here.


from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Book


class BookListView(ListView):
    model = Book
    template_name = 'materials/book_list.html'
    context_object_name = 'books'
    
class BookDetailView(DetailView):
    model = Book
    template_name = 'materials/book_detail.html'
    context_object_name = 'book'

class BookCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Book
    template_name = 'materials/book_form.html'
    fields = [
        "title", "author", "description", "book_type",
        "price", "file", "external_link", "stock", "shipping_available"
    ]
    success_url = reverse_lazy('materials:book-list')

    def test_func(self):
        return self.request.user.role in ["manager", "employee"]


class BookUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    template_name = 'materials/book_form.html'
    fields = [
        "title", "author", "description", "book_type",
        "price", "file", "external_link", "stock", "shipping_available"
    ]
    success_url = reverse_lazy('materials:book-list')

    def test_func(self):
        return self.request.user.role in ["manager", "employee"]


class BookDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Book
    template_name = 'materials/book_confirm_delete.html'
    success_url = reverse_lazy('materials:book-list')

    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
