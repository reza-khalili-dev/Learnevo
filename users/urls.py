from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = "users"

urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"), 
    path('login/',views.CustomLoginView.as_view(), name='login'),
    path('logout/',LogoutView.as_view(), name='logout'),
    path("dashboard/student/", views.StudentDashboardView.as_view(), name="student-dashboard"),
    path("dashboard/instructor/", views.InstructorDashboardView.as_view(), name="instructor-dashboard"),
    path("employee/dashboard/", views.EmployeeDashboardView.as_view(), name="employee-dashboard"),
    path("dashboard/admin/", views.AdminDashboardView.as_view(), name="admin-dashboard"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("add/", views.UserCreateView.as_view(), name="user_add"),
    path("profile/<int:pk>/", views.ProfileView.as_view(), name="profile_detail"),
    path("profile/<int:pk>/edit/", views.ProfileEditView.as_view(), name="profile_edit"),
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/create/', views.StudentCreateView.as_view(), name='student_create'),
    
    
]
