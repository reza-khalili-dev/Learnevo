from django.urls import path
from . import views

app_name = "exams"

urlpatterns = [
    path("", views.ExamListView.as_view(), name="exam_list"),
    path("create/", views.ExamCreateView.as_view(), name="exam_create"),
    path("<int:pk>/", views.ExamDetailView.as_view(), name="exam_detail"),
    path("<int:pk>/edit/", views.ExamUpdateView.as_view(), name="exam_edit"),

    # Questions
    path("<int:exam_id>/questions/add/", views.QuestionCreateView.as_view(), name="question_add"),
    path("questions/<int:pk>/edit/", views.QuestionUpdateView.as_view(), name="question_edit"),
    path("questions/<int:pk>/", views.QuestionDetailView.as_view(), name="question_detail"),

    # Choices
    path("question/<int:question_id>/choice/add/", views.ChoiceCreateView.as_view(), name="choice_add"),
    path("choice/<int:pk>/edit/", views.ChoiceUpdateView.as_view(), name="choice_edit"),
    
    # Student Exam Flow
    path("<int:pk>/start/", views.start_exam, name="start_exam"),
    path("<int:exam_id>/question/<int:question_id>/", views.take_question, name="take_question"),
    path("<int:exam_id>/question/<int:question_id>/submit/", views.submit_answer, name="submit_answer"),
    path("<int:pk>/finish/", views.finish_exam, name="finish_exam"),
]
