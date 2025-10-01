from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from .models import Grade
from courses.models import Assignment
from exams.models import Exam


# Create your views here.

class StudentGradeListView(LoginRequiredMixin, ListView):
    model = Grade
    template_name = 'grades/student_grade_list.html'
    context_object_name = 'grades'
    
    def get_queryset(self):
        return Grade.objects.filter(student=self.request.user)
    
class InstructorGradeListView(LoginRequiredMixin, ListView):
    model = Grade
    template_name = "grades/instructor_grade_list.html"
    context_object_name = "grades"
    
    def get_queryset(self):
        instructor = self.request.user
        return Grade.objects.filter(
            exam__instructor=instructor
        ) | Grade.objects.filter(
            assignment__course__instructor=instructor
        )

class InstructorOrAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in ["instructor", "manager", "employee"]
    

class GradeCreateView(LoginRequiredMixin, InstructorOrAdminRequiredMixin, CreateView):
    model = Grade
    fields = ["student", "assignment", "exam", "score", "max_score"]
    template_name = 'grades/grade_form.htm'
    success_url = reverse_lazy('instructor-grade-list')

    def form_valid(self, form):
        return super().form_valid(form)

class GradeUpdateView(LoginRequiredMixin, InstructorOrAdminRequiredMixin, UpdateView):
    model = Grade
    fields = ["score", "max_score"]
    template_name = 'grades/grade_form.html'
    success_url = reverse_lazy('instructor-grade-list')

    def get_queryset(self):
        instructor = self.request.user
        return Grade.objects.filter(
            exam__instructor=instructor
        ) | Grade.objects.filter(
            assignment__course__instructor=instructor
        )