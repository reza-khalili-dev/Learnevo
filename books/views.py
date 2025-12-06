from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.db.models import Sum, Count, Q, F, DecimalField
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from decimal import Decimal
import json
from .models import Book, BookCategory
from orders.models import Order, OrderItem


class BookListView(ListView):
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = 20
    
    def get_queryset(self):
        return Book.objects.select_related('category').all()


class BookDetailView(DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'
    
    def get_queryset(self):
        return Book.objects.select_related('category', 'uploaded_by')


class BookCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Book
    template_name = 'books/book_form.html'
    fields = [
        "title", "author", "description", "book_type", "category",
        "price", "image", "file", "external_link", 
        "stock", "min_stock_alert", "shipping_available", "status"
    ]
    success_url = reverse_lazy('books:book_list')

    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)


class BookUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    template_name = 'books/book_form.html'
    fields = [
        "title", "author", "description", "book_type", "category",
        "price", "image", "file", "external_link", 
        "stock", "min_stock_alert", "shipping_available", "status"
    ]
    success_url = reverse_lazy('books:book_list')

    def test_func(self):
        return self.request.user.role in ["manager", "employee"]


class BookDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Book
    template_name = 'books/book_confirm_delete.html'
    success_url = reverse_lazy('books:book_list')

    def test_func(self):
        return self.request.user.role in ["manager", "employee"]


class BookDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'books/dashboard.html'
    
    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        total_books = Book.objects.count()
        physical_books = Book.objects.filter(book_type__in=["physical", "both"]).count()
        digital_books = Book.objects.filter(book_type__in=["digital", "both"]).count()
        
        inventory_value = Book.objects.filter(
            book_type__in=["physical", "both"]
        ).aggregate(
            total_value=Sum(F('price') * F('stock'), output_field=DecimalField())
        )['total_value'] or Decimal('0.00')
        
        low_stock_books = Book.objects.filter(
            Q(book_type__in=["physical", "both"]) &
            Q(stock__gt=0) &
            Q(stock__lt=F('min_stock_alert'))
        ).count()
        
        from django.utils.timezone import now
        today = now().date()
        today_orders = Order.objects.filter(created_at__date=today).count()
        
        recent_books = Book.objects.select_related('category').order_by('-created_at')[:10]
        
        recent_orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')[:10]
        
        top_books = Book.objects.annotate(
            total_sold=Coalesce(Sum('order_items__quantity'), 0)
        ).filter(total_sold__gt=0).order_by('-total_sold')[:5]
        
        context.update({
            'total_books': total_books,
            'physical_books': physical_books,
            'digital_books': digital_books,
            'inventory_value': inventory_value,
            'low_stock_books': low_stock_books,
            'today_orders': today_orders,
            'recent_books': recent_books,
            'recent_orders': recent_orders,
            'top_books': top_books,
            'categories': BookCategory.objects.all(),
        })
        return context


class BookSearchView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def get_queryset(self):
        queryset = Book.objects.select_related('category').all()
        
        search_query = self.request.GET.get('q', '')
        book_type = self.request.GET.get('book_type', '')
        category_id = self.request.GET.get('category', '')
        min_price = self.request.GET.get('min_price', '')
        max_price = self.request.GET.get('max_price', '')
        status = self.request.GET.get('status', '')
        in_stock = self.request.GET.get('in_stock', '')
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(author__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        if book_type:
            queryset = queryset.filter(book_type=book_type)
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if in_stock == 'yes':
            queryset = queryset.filter(stock__gt=0)
        elif in_stock == 'no':
            queryset = queryset.filter(stock=0)
        
        sort_by = self.request.GET.get('sort_by', '-created_at')
        if sort_by in ['title', 'author', 'price', 'stock', 'created_at', '-title', '-author', '-price', '-stock', '-created_at']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_params'] = self.request.GET.dict()
        return context


class QuickOrderCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    
    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            book_id = data.get('book_id')
            quantity = int(data.get('quantity', 1))
            customer_id = data.get('customer_id')
            
            if not book_id:
                return JsonResponse({'success': False, 'error': 'Book ID is required'})
            
            book = get_object_or_404(Book, id=book_id)
            
            if book.is_physical and book.stock < quantity:
                return JsonResponse({
                    'success': False, 
                    'error': f'Only {book.stock} items available in stock'
                })
            
            order = Order.objects.create(
                user_id=customer_id or request.user.id,
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
            
            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'message': f'Order created successfully. Total: ${order.total}'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class BookReturnView(LoginRequiredMixin, UserPassesTestMixin, View):
    
    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            order_item_id = data.get('order_item_id')
            return_quantity = int(data.get('quantity', 1))
            reason = data.get('reason', '')
            
            order_item = get_object_or_404(OrderItem, id=order_item_id)
            
            if return_quantity > order_item.quantity:
                return JsonResponse({
                    'success': False,
                    'error': f'Cannot return more than {order_item.quantity} items'
                })
            
            
            if order_item.book.is_physical:
                order_item.book.stock += return_quantity
                order_item.book.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{return_quantity} items returned successfully. Stock updated.',
                'new_stock': order_item.book.stock
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})