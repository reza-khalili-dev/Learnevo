from django.urls import path
from . import views
app_name = "exams"

urlpatterns = [
    path("", views.ExamListView.as_view(), name="exam_list"),
    path("exam/<int:exam_id>/take/", views.TakeExamView.as_view(), name="take_exam"),
    path("exam/<int:exam_id>/result/", views.ExamResultView.as_view(), name="exam_result"),
    path("instructor/", views.InstructorExamListView.as_view(), name="instructor_exams"),
]