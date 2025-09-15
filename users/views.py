from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .mixins import RoleRequiredMixin

# Create your views here.


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
class HomePageView(TemplateView):
    template_name = 'users/home.html'

class StudentDashboard(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = 'student'
    template_name = 'users/dashboards/student.html'

class InstructorDashboard(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = 'instructor'
    template_name = 'users/dashboards/instructor.html'

class AdminDashboard(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = ['manager', 'employee']
    template_name = 'users/dashboards/admin.html'