// Dashboard JavaScript Functions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })

    // Quick Order Modal
    const quickOrderModal = document.getElementById('quickOrderModal')
    if (quickOrderModal) {
        quickOrderModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget
            const bookId = button.getAttribute('data-book-id')
            const bookTitle = button.getAttribute('data-book-title')
            const modalBookTitle = quickOrderModal.querySelector('#modalBookTitle')
            const bookIdInput = quickOrderModal.querySelector('#book_id')
            
            if (modalBookTitle) {
                modalBookTitle.textContent = bookTitle
            }
            if (bookIdInput) {
                bookIdInput.value = bookId
            }
        })
    }

    // Quick Return Modal
    const quickReturnModal = document.getElementById('quickReturnModal')
    if (quickReturnModal) {
        quickReturnModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget
            const orderItemId = button.getAttribute('data-order-item-id')
            const orderId = button.getAttribute('data-order-id')
            const bookTitle = button.getAttribute('data-book-title')
            const maxQuantity = button.getAttribute('data-max-quantity')
            
            const modalTitle = quickReturnModal.querySelector('#returnModalTitle')
            const orderItemIdInput = quickReturnModal.querySelector('#order_item_id')
            const quantityInput = quickReturnModal.querySelector('#return_quantity')
            
            if (modalTitle) {
                modalTitle.textContent = `Return: ${bookTitle}`
            }
            if (orderItemIdInput) {
                orderItemIdInput.value = orderItemId
            }
            if (quantityInput) {
                quantityInput.max = maxQuantity
                quantityInput.value = 1
            }
        })
    }

    // Search Form Toggle
    const searchToggleBtn = document.getElementById('searchToggleBtn')
    const searchPanel = document.getElementById('searchPanel')
    
    if (searchToggleBtn && searchPanel) {
        searchToggleBtn.addEventListener('click', function() {
            searchPanel.classList.toggle('d-none')
            const icon = this.querySelector('i')
            if (searchPanel.classList.contains('d-none')) {
                icon.className = 'fas fa-chevron-down'
            } else {
                icon.className = 'fas fa-chevron-up'
            }
        })
    }

    // Quick Order Form Submission
    const quickOrderForm = document.getElementById('quickOrderForm')
    if (quickOrderForm) {
        quickOrderForm.addEventListener('submit', function(e) {
            e.preventDefault()
            
            const formData = new FormData(this)
            const data = {
                book_id: formData.get('book_id'),
                quantity: parseInt(formData.get('quantity')),
                customer_id: formData.get('customer_id') || null
            }
            
            const submitBtn = this.querySelector('button[type="submit"]')
            const originalText = submitBtn.innerHTML
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...'
            submitBtn.disabled = true
            
            fetch(this.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', data.message)
                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('quickOrderModal'))
                    modal.hide()
                    // Reload page after 2 seconds to see updated data
                    setTimeout(() => location.reload(), 2000)
                } else {
                    showAlert('danger', data.error)
                    submitBtn.innerHTML = originalText
                    submitBtn.disabled = false
                }
            })
            .catch(error => {
                showAlert('danger', 'An error occurred: ' + error)
                submitBtn.innerHTML = originalText
                submitBtn.disabled = false
            })
        })
    }

    // Quick Return Form Submission
    const quickReturnForm = document.getElementById('quickReturnForm')
    if (quickReturnForm) {
        quickReturnForm.addEventListener('submit', function(e) {
            e.preventDefault()
            
            const formData = new FormData(this)
            const data = {
                order_item_id: formData.get('order_item_id'),
                quantity: parseInt(formData.get('quantity')),
                reason: formData.get('reason')
            }
            
            const submitBtn = this.querySelector('button[type="submit"]')
            const originalText = submitBtn.innerHTML
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...'
            submitBtn.disabled = true
            
            fetch(this.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', data.message)
                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('quickReturnModal'))
                    modal.hide()
                    // Reload page after 2 seconds
                    setTimeout(() => location.reload(), 2000)
                } else {
                    showAlert('danger', data.error)
                    submitBtn.innerHTML = originalText
                    submitBtn.disabled = false
                }
            })
            .catch(error => {
                showAlert('danger', 'An error occurred: ' + error)
                submitBtn.innerHTML = originalText
                submitBtn.disabled = false
            })
        })
    }

    // Stock Filter
    const stockFilter = document.getElementById('stockFilter')
    if (stockFilter) {
        stockFilter.addEventListener('change', function() {
            this.form.submit()
        })
    }

    // Price Range Validation
    const minPriceInput = document.getElementById('min_price')
    const maxPriceInput = document.getElementById('max_price')
    
    if (minPriceInput && maxPriceInput) {
        const validatePriceRange = function() {
            const min = parseFloat(minPriceInput.value)
            const max = parseFloat(maxPriceInput.value)
            
            if (min && max && min > max) {
                minPriceInput.classList.add('is-invalid')
                maxPriceInput.classList.add('is-invalid')
            } else {
                minPriceInput.classList.remove('is-invalid')
                maxPriceInput.classList.remove('is-invalid')
            }
        }
        
        minPriceInput.addEventListener('change', validatePriceRange)
        maxPriceInput.addEventListener('change', validatePriceRange)
    }

    // Export to Excel Button
    const exportBtn = document.getElementById('exportBtn')
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Exporting...'
            this.disabled = true
            
            // Simulate export process
            setTimeout(() => {
                showAlert('success', 'Export completed! Your file will download shortly.')
                this.innerHTML = '<i class="fas fa-file-excel me-2"></i> Export to Excel'
                this.disabled = false
            }, 1500)
        })
    }
    
    // Chart Actions
    const chartButtons = document.querySelectorAll('.chart-btn[data-chart]')
    chartButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const chartType = this.getAttribute('data-chart')
            switch(chartType) {
                case 'bookType':
                    // Refresh book type chart
                    if (window.refreshCharts) {
                        refreshCharts()
                        showAlert('info', 'Book type chart refreshed')
                    }
                    break;
                case 'topSellers':
                    // Show details modal for top sellers
                    showAlert('info', 'Showing top sellers details')
                    break;
                case 'lowStock':
                    // Navigate to low stock books
                    window.location.href = "{% url 'books:book_search' %}?in_stock=yes&status=active&sort_by=stock"
                    break;
            }
        })
    })
})

// Helper Functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div')
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`
    alertDiv.role = 'alert'
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `
    
    // Add to page
    const container = document.querySelector('.container-fluid') || document.querySelector('.container')
    if (container) {
        container.insertBefore(alertDiv, container.firstChild)
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv)
            }
        }, 5000)
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount)
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    })
}