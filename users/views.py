from pyexpat.errors import messages
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .mixins import RoleRequiredMixin
from django.urls import reverse
from django.contrib import messages


# Create your views here.

User = get_user_model()


class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    template_name = "users/user_form.html"
    fields = ["first_name", "last_name", "email", "phone_number", "role", "password"]
    success_url = reverse_lazy("users:user_list")

    def form_valid(self, form):
        messages.success(self.request, "User created successfully!")
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.role in ["manager", "employee"]

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    ordering = ["-id"]

    def test_func(self):
        return self.request.user.role in ["manager", "employee"]


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    
    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')        
        if next_url:
            return next_url
        
        user = self.request.user
        role = getattr(user, 'role', None)

        if role == 'student':
            return reverse('student-dashboard')
        if role == 'instructor':
            return reverse('instructor-dashboard')
        if role in ('manager', 'employee'):
            return reverse('admin-dashboard')
        
        return super().get_success_url()  
    
class HomePageView(TemplateView):
    template_name = 'users/home.html'

class StudentDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = 'student'
    template_name = 'users/dashboards/student.html'

class InstructorDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = 'instructor'
    template_name = 'users/dashboards/instructor.html'

class AdminDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = ['manager', 'employee']
    template_name = 'users/dashboards/admin.html'
    
