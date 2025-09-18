from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin , UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Course , Class


# Create your views here.

class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'

class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'

class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    fields = ["title", "description"]
    template_name = 'courses/course_form.html'

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.role == 'Instructor'

class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    fields = ["title", "description"]
    template_name = 'courses/course_form.html'

    def test_func(self):
        course = self.get.object()
        return self.request.user == course.instructor

class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('course_list')

    def test_func(self):
        course = self.get.object()
        return self.request.user == course.instructor

class ClassListView(LoginRequiredMixin, ListView):
    model = Class
    template_name = 'courses/class_list.html'
    context_object_name = 'classes'

class ClassDetailView(LoginRequiredMixin, DetailView):
    model = Class
    template_name = 'courses/class_detail.html'
    context_object_name = 'class_obj'

class ClassCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Class
    fields = ['course', 'title', 'start_date', 'end_date', 'capacity']
    template_name = 'courses/class_form.html'

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        if getattr(self.request.user, 'role', None) == 'Instructor':
            form.fields['course'].queryset = Course.objects.filter(instructor=self.request.user)
        else:
            form.fields['course'].queryset = Course.objects.none()
        return form
    def test_func(self):
        return getattr(self.request.user, 'role', None) == 'Instructor'
    
    def form_valid(self, form):
        course = form.cleaned_data.get('course')
        if course.instructor != self.request.user:
            form.add_error('course', 'You can only create classes for your courses.')
            return self.form_invalid(form)
        return super().form_valid(form)
    
class ClassUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Class
    fields = ['title', 'start_date', 'end_date', 'capacity']
    template_name = 'courses/class_form.html'

    def test_func(self):
        class_obj = self.get_object()
        return self.request.user == class_obj.course.instructor

class ClassDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Class
    template_name = 'courses/class_confirm_delete.html'
    success_url = reverse_lazy('class_list')

    def test_func(self):
        class_obj = self.get_object()
        return self.request.user == class_obj.course.instructor