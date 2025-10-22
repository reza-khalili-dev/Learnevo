from django.views import View
from django.views.generic import ListView
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Exam, Choice, StudentAnswer
from .services import calculate_exam_score


# Create your views here.

class TakeExamView(LoginRequiredMixin, View):
    def get(self, request, exam_id):
        exam = get_object_or_404.filter(Exam, exam_id)
        questions = exam.questions.all()
        return render(request, "exams/take_exam.html", {"exam": exam, "questions": questions})

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        questions = exam.questions.all()
        
        for question in questions:
            choice_id = request.POST.get(str(question.id))

            if choice_id:
                choice = get_object_or_404(Choice, id=choice_id, question=question)

                StudentAnswer.objects.update_or_create(
                    student=request.user,
                    question=question,
                    defaults={"choice": choice},
                )
        
        result = calculate_exam_score(request.user, exam)
        messages.success(request, f"Your exam is submitted. Score: {result.score}")
        return redirect("exam_result", exam_id=exam.id)

class ExamResultView(LoginRequiredMixin, View):
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        result = exam.results.filter(student=request.user).first()
        return render(request, "exams/exam_result.html", {"exam": exam, "result": result})

class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = "exams/exam_list.html"
    context_object_name = "exams"