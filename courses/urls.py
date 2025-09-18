from django.urls import path
from . import views

urlpatterns = [
    path('',views.CourseListView.as_view(), name='course_list'),
    path('<int:pk>/',views.CourseDetailView.as_view(), name='course_detail'),
    path('create/',views.CourseCreateView.as_view(), name='course_create'),
    path('<int:pk>/update/',views.CourseUpdateView.as_view(), name='course_update'),
    path('<int:pk>/delete/',views.CourseDeleteView.as_view(), name='course_delete'),
    path('classes/', views.ClassListView.as_view(), name='class_list'),
    path('classes/create/', views.ClassCreateView.as_view(), name='class_create'),
    path('classes/<int:pk>/', views.ClassDetailView.as_view(), name='class_detail'),
    path('classes/<int:pk>/update/', views.ClassUpdateView.as_view(), name='class_update'),
    path('classes/<int:pk>/delete/', views.ClassDeleteView.as_view(), name='class_delete'),
]
