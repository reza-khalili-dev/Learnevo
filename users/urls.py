from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"), 
    path('login/',views.CustomLoginView.as_view(), name='login'),
    path('logout/',LogoutView.as_view(), name='logout'),
    
]
