from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .mixins import RoleRequiredMixin
from django.urls import reverse

# Create your views here.


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
    
