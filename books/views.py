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
from .forms import BookForm, BookSearchForm, QuickOrderForm, BookReturnForm
from .forms import BookCategoryForm, CategoryBulkActionForm
from django.views.generic.edit import FormView
from django.http import HttpResponseRedirect



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
    form_class = BookForm
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('books:dashboard')

    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Book'
        return context


class BookUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('books:dashboard')

    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Book: {self.object.title}'
        return context


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
        form = BookSearchForm(self.request.GET)
        
        if form.is_valid():
            data = form.cleaned_data
            
            if data.get('q'):
                search_query = data['q']
                queryset = queryset.filter(
                    Q(title__icontains=search_query) |
                    Q(author__icontains=search_query) |
                    Q(description__icontains=search_query)
                )
            
            if data.get('book_type'):
                queryset = queryset.filter(book_type=data['book_type'])
            
            if data.get('category'):
                queryset = queryset.filter(category=data['category'])
            
            if data.get('min_price'):
                queryset = queryset.filter(price__gte=data['min_price'])
            
            if data.get('max_price'):
                queryset = queryset.filter(price__lte=data['max_price'])
            
            if data.get('status'):
                queryset = queryset.filter(status=data['status'])
            
            if data.get('in_stock') == 'yes':
                queryset = queryset.filter(stock__gt=0)
            elif data.get('in_stock') == 'no':
                queryset = queryset.filter(stock=0)
            
            if data.get('sort_by'):
                queryset = queryset.order_by(data['sort_by'])
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = BookSearchForm(self.request.GET)
        context['title'] = 'Advanced Book Search'
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
        


# category

class CategoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):

    model = BookCategory
    template_name = 'books/category_list.html'
    context_object_name = 'categories'
    
    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bulk_action_form'] = CategoryBulkActionForm()
        
  
        categories = context['categories']
        
        total_books_in_categories = 0
        total_low_stock_books = 0
        categories_with_books = 0
        
        for category in categories:
            book_count = category.books.count()
            category.book_count = book_count
            category.active_books = category.books.filter(status='active').count()
            low_stock = category.books.filter(
                stock__gt=0, 
                stock__lt=F('min_stock_alert')
            ).count()
            category.low_stock_books = low_stock
            
            total_books_in_categories += book_count
            total_low_stock_books += low_stock
            if book_count > 0:
                categories_with_books += 1
        
        context.update({
            'total_books_in_categories': total_books_in_categories,
            'total_low_stock_books': total_low_stock_books,
            'categories_with_books': categories_with_books,
        })
        
        return context


class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = BookCategory
    form_class = BookCategoryForm
    template_name = 'books/category_form.html'
    success_url = reverse_lazy('books:category_list')
    
    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Category'
        return context


class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BookCategory
    form_class = BookCategoryForm
    template_name = 'books/category_form.html'
    success_url = reverse_lazy('books:category_list')
    
    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Category: {self.object.name}'
        return context


class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = BookCategory
    template_name = 'books/category_confirm_delete.html'
    success_url = reverse_lazy('books:category_list')
    
    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def form_valid(self, form):
        if self.object.books.exists():
            messages.error(
                self.request, 
                f'Cannot delete category "{self.object.name}" because it has {self.object.books.count()} books. '
                'Please reassign books to another category first.'
            )
            return HttpResponseRedirect(self.success_url)
        return super().form_valid(form)


class CategoryBulkActionView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    form_class = CategoryBulkActionForm
    template_name = 'books/category_bulk_action.html'
    success_url = reverse_lazy('books:category_list')
    
    def test_func(self):
        return self.request.user.role in ["manager", "employee"]
    
    def form_valid(self, form):
        category_ids = self.request.POST.getlist('category_ids')
        action = form.cleaned_data['action']
        target_category = form.cleaned_data['target_category']
        
        if not category_ids:
            messages.error(self.request, 'No categories selected.')
            return super().form_invalid(form)
        
        categories = BookCategory.objects.filter(id__in=category_ids)
        
        if action == 'delete':
            deleted_count = 0
            for category in categories:
                if not category.books.exists():
                    category.delete()
                    deleted_count += 1
                else:
                    messages.warning(
                        self.request,
                        f'Category "{category.name}" not deleted because it has {category.books.count()} books.'
                    )
            
            messages.success(self.request, f'Successfully deleted {deleted_count} categories.')
        
        elif action == 'merge':
            if not target_category:
                messages.error(self.request, 'Target category is required for merge action.')
                return super().form_invalid(form)
            
            merged_count = 0
            for category in categories:
                if category.id != target_category.id:
                    category.books.update(category=target_category)
                    category.delete()
                    merged_count += 1
            
            messages.success(
                self.request, 
                f'Successfully merged {merged_count} categories into "{target_category.name}".'
            )
        
        return super().form_valid(form)