from django.urls import path
from .views import (
    ExamListView, ExamCreateView, ExamUpdateView, ExamDetailView,
    QuestionCreateView, QuestionUpdateView, QuestionDetailView,
    ChoiceCreateView, ChoiceUpdateView,submit_answer,
    start_exam, take_question, finish_exam
)

app_name = "exams"

urlpatterns = [
    # Exams
    path("", ExamListView.as_view(), name="exam_list"),
    path("create/", ExamCreateView.as_view(), name="exam_create"),
    path("<int:pk>/", ExamDetailView.as_view(), name="exam_detail"),
    path("<int:pk>/edit/", ExamUpdateView.as_view(), name="exam_edit"),

    # Questions
    path("<int:exam_id>/questions/add/", QuestionCreateView.as_view(), name="question_add"),
    path("questions/<int:pk>/edit/", QuestionUpdateView.as_view(), name="question_edit"),
    path("questions/<int:pk>/", QuestionDetailView.as_view(), name="question_detail"),

    # Choices
    path("question/<int:question_id>/choice/add/", ChoiceCreateView.as_view(), name="choice_add"),
    path("choice/<int:pk>/edit/", ChoiceUpdateView.as_view(), name="choice_edit"),

    # Student exam flow
    path("<int:pk>/start/", start_exam, name="start_exam"),
    path("<int:exam_id>/question/<int:question_id>/", take_question, name="take_question"),
    path("<int:pk>/finish/", finish_exam, name="finish_exam"),
    path("exam/<int:exam_id>/question/<int:question_id>/submit/", submit_answer, name="submit_answer"),
]
