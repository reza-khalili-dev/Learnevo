from django.urls import path
from .views import StudentGradeListView, InstructorGradeListView, GradeCreateView, GradeUpdateView

urlpatterns = [
    path("student/", StudentGradeListView.as_view(), name="student-grade-list"),
    path("instructor/", InstructorGradeListView.as_view(), name="instructor-grade-list"),
    path("add/", GradeCreateView.as_view(), name="grade-add"),
    path("<int:pk>/edit/", GradeUpdateView.as_view(), name="grade-edit"),
]