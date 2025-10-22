from django.urls import path
from .views import TakeExamView, ExamResultView, ExamListView

app_name = "exams"

urlpatterns = [
    path("", ExamListView.as_view(), name="exam_list"),
    path("exam/<int:exam_id>/take/", TakeExamView.as_view(), name="take_exam"),
    path("exam/<int:exam_id>/result/", ExamResultView.as_view(), name="exam_result"),
]