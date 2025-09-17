from django.urls import path
from . import views

urlpatterns = [
    path('',views.CourseListView.as_view(), name='course_list'),
    path('<int:pk>/',views.CourseDetailView.as_view(), name='course_detail'),
    path('create/',views.CourseCreateView.as_view(), name='course_create'),
    path('<int:pk>/update/',views.CourseUpdateView.as_view(), name='course_update'),
    path('<int:pk>/delete/',views.CourseDeleteView.as_view(), name='course_delete'),
]
