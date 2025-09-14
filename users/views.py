from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView

# Create your views here.


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
class HomePageView(TemplateView):
    template_name = 'users/home.html'

