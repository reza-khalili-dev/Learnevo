from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView,CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Exam, Choice, StudentAnswer
from .services import calculate_exam_score
from django.urls import reverse_lazy
from .forms import ExamForm

# Create your views here.

class TakeExamView(LoginRequiredMixin, View):
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        questions = exam.questions.all()
        return render(request, "exams/take_exam.html", {"exam": exam, "questions": questions})

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        questions = exam.questions.all()
        
        for question in questions:
            if question.qtype in ("mcq", "audio_mcq", "image_mcq"):
                choice_id = request.POST.get(str(question.id))
                if choice_id:
                    choice = get_object_or_404(Choice, id=choice_id, question=question)
                    StudentAnswer.objects.update_or_create(
                        student=request.user,
                        question=question,
                        defaults={"choice": choice, "text_answer": None},
                    )
            else:
                text_ans = request.POST.get(f"q_{question.id}_text")
                if text_ans:
                    StudentAnswer.objects.update_or_create(
                        student=request.user,
                        question=question,
                        defaults={"text_answer": text_ans, "choice": None},
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

class InstructorExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = "exams/instructor_exams.html"
    context_object_name = "exams"

    def get_queryset(self):
        return Exam.objects.filter(instructor=self.request.user)
    

# --- CRUD Views for Exams ---
class ExamCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = "exams/exam_form.html"
    success_url = reverse_lazy("exams:exam_list")

    def test_func(self):
        return self.request.user.role in ["manager", "employee", "instructor"]


class ExamUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = "exams/exam_form.html"
    success_url = reverse_lazy("exams:exam_list")

    def test_func(self):
        return self.request.user.role in ["manager", "employee", "instructor"]


class ExamDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Exam
    template_name = "exams/exam_confirm_delete.html"
    success_url = reverse_lazy("exams:exam_list")

    def test_func(self):
        return self.request.user.role in ["manager", "employee", "instructor"]