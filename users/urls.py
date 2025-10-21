from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"), 
    path('login/',views.CustomLoginView.as_view(), name='login'),
    path('logout/',LogoutView.as_view(), name='logout'),
    path("dashboard/student/", views.StudentDashboardView.as_view(), name="student-dashboard"),
    path("dashboard/instructor/", views.InstructorDashboardView.as_view(), name="instructor-dashboard"),
    path("dashboard/admin/", views.AdminDashboardView.as_view(), name="admin-dashboard"),
    path("add/", views.UserCreateView.as_view(), name="user_add"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    
]
