from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, ButtonHolder, Div, Field, HTML
from crispy_forms.bootstrap import Tab, TabHolder, Accordion, AccordionGroup
from .models import Book, BookCategory


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "title", "author", "description", "category",
            "book_type", "price", "image", "file", 
            "external_link", "stock", "min_stock_alert",
            "shipping_available", "status"
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'min': '0'}),
            'min_stock_alert': forms.NumberInput(attrs={'min': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3 col-form-label'
        self.helper.field_class = 'col-md-9'
        
        self.helper.layout = Layout(
            TabHolder(
                Tab('Basic Information',
                    Row(
                        Column('title', css_class='form-group col-md-8 mb-3'),
                        Column('author', css_class='form-group col-md-4 mb-3'),
                    ),
                    Row(
                        Column('category', css_class='form-group col-md-6 mb-3'),
                        Column('book_type', css_class='form-group col-md-6 mb-3'),
                    ),
                    'description',
                    css_class='mb-4'
                ),
                Tab('Pricing & Stock',
                    Row(
                        Column('price', css_class='form-group col-md-6 mb-3'),
                        Column('stock', css_class='form-group col-md-3 mb-3'),
                        Column('min_stock_alert', css_class='form-group col-md-3 mb-3'),
                    ),
                    Row(
                        Column('status', css_class='form-group col-md-6 mb-3'),
                        Column('shipping_available', css_class='form-group col-md-6 mb-3'),
                    ),
                    css_class='mb-4'
                ),
                Tab('Files & Media',
                    Row(
                        Column('image', css_class='form-group col-md-6 mb-3'),
                        Column('file', css_class='form-group col-md-6 mb-3'),
                    ),
                    'external_link',
                    HTML("""
                    <div class="alert alert-info mt-3">
                        <small>
                            <i class="fas fa-info-circle me-2"></i>
                            <strong>Note:</strong> For digital books, upload a file or provide an external link.
                            For physical books, stock quantity is required.
                        </small>
                    </div>
                    """),
                    css_class='mb-4'
                ),
            ),
            ButtonHolder(
                Submit('submit', 'Save Book', css_class='btn btn-primary'),
                HTML('<a href="{% url "books:dashboard" %}" class="btn btn-secondary">Cancel</a>'),
                css_class='d-flex justify-content-end gap-2 mt-4'
            )
        )
        
        # Dynamic help text
        self.fields['image'].help_text = "Recommended size: 300x400px. Max size: 2MB."
        self.fields['file'].help_text = "Upload PDF or EPUB file. Max size: 50MB."
        self.fields['external_link'].help_text = "External URL for digital content (if no file uploaded)."
        self.fields['min_stock_alert'].help_text = "Alert when stock goes below this number."


class BookSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by title, author, or description...',
            'class': 'form-control'
        })
    )
    
    book_type = forms.ChoiceField(
        required=False,
        label='Book Type',
        choices=[('', 'All Types')] + Book.BOOK_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    category = forms.ModelChoiceField(
        required=False,
        label='Category',
        queryset=BookCategory.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    min_price = forms.DecimalField(
        required=False,
        label='Min Price',
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )
    
    max_price = forms.DecimalField(
        required=False,
        label='Max Price',
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1000.00',
            'step': '0.01'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        label='Status',
        choices=[('', 'All Status')] + Book.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    in_stock = forms.ChoiceField(
        required=False,
        label='In Stock',
        choices=[('', 'All'), ('yes', 'Yes'), ('no', 'No')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        label='Sort By',
        choices=[
            ('-created_at', 'Newest First'),
            ('created_at', 'Oldest First'),
            ('title', 'Title A-Z'),
            ('-title', 'Title Z-A'),
            ('price', 'Price Low-High'),
            ('-price', 'Price High-Low'),
            ('stock', 'Stock Low-High'),
            ('-stock', 'Stock High-Low'),
        ],
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_action = ''
        self.helper.form_class = 'form-horizontal row g-3'
        self.helper.label_class = 'form-label'
        
        self.helper.layout = Layout(
            Row(
                Column('q', css_class='col-md-6'),
                Column('book_type', css_class='col-md-3'),
                Column('category', css_class='col-md-3'),
            ),
            Row(
                Column('min_price', css_class='col-md-3'),
                Column('max_price', css_class='col-md-3'),
                Column('status', css_class='col-md-3'),
                Column('in_stock', css_class='col-md-3'),
            ),
            Row(
                Column('sort_by', css_class='col-md-3'),
                Column(
                    ButtonHolder(
                        Submit('submit', 'Search', css_class='btn btn-primary'),
                        HTML('<a href="." class="btn btn-outline-secondary">Clear</a>'),
                        css_class='d-flex gap-2'
                    ),
                    css_class='col-md-9 d-flex align-items-end justify-content-end'
                ),
            )
        )


class QuickOrderForm(forms.Form):
    book_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    customer_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-form-label'
        self.helper.field_class = 'mb-3'
        
        self.helper.layout = Layout(
            'book_id',
            'quantity',
            'customer_id',
        )


class BookReturnForm(forms.Form):
    order_item_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    reason = forms.ChoiceField(
        choices=[
            ('damaged', 'Damaged Product'),
            ('wrong_item', 'Wrong Item Shipped'),
            ('customer_change_mind', 'Customer Changed Mind'),
            ('defective', 'Defective Product'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Any additional notes...'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-form-label'
        self.helper.field_class = 'mb-3'
        
        self.helper.layout = Layout(
            'order_item_id',
            'quantity',
            'reason',
            'notes',
        )



class BookCategoryForm(forms.ModelForm):
    class Meta:
        model = BookCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3 col-form-label'
        self.helper.field_class = 'col-md-9'
        
        self.helper.layout = Layout(
            'name',
            'description',
            ButtonHolder(
                Submit('submit', 'Save Category', css_class='btn btn-primary'),
                HTML('<a href="{% url "books:category_list" %}" class="btn btn-secondary">Cancel</a>'),
                css_class='d-flex justify-content-end gap-2 mt-4'
            )
        )


class CategoryBulkActionForm(forms.Form):
    ACTION_CHOICES = [
        ('delete', 'Delete Selected'),
        ('merge', 'Merge Selected'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    target_category = forms.ModelChoiceField(
        required=False,
        queryset=BookCategory.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Required for merge action"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        
        self.helper.layout = Layout(
            Row(
                Column('action', css_class='col-md-6'),
                Column('target_category', css_class='col-md-6'),
            ),
            ButtonHolder(
                Submit('submit', 'Apply Action', css_class='btn btn-warning'),
                css_class='d-flex justify-content-end mt-3'
            )
        )