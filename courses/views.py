from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin , UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Course , Classroom , Session
from .forms import SessionForm



# Create your views here.

# Course views

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


# Classroom views

class ClassListView(LoginRequiredMixin, ListView):
    model = Classroom
    template_name = 'courses/class_list.html'
    context_object_name = 'classes'

class ClassDetailView(LoginRequiredMixin, DetailView):
    model = Classroom
    template_name = 'courses/class_detail.html'
    context_object_name = 'class_obj'

class ClassCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Classroom
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
    model = Classroom
    fields = ['title', 'start_date', 'end_date', 'capacity']
    template_name = 'courses/class_form.html'

    def test_func(self):
        class_obj = self.get_object()
        return self.request.user == class_obj.course.instructor

class ClassDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Classroom
    template_name = 'courses/class_confirm_delete.html'
    success_url = reverse_lazy('class_list')

    def test_func(self):
        class_obj = self.get_object()
        return self.request.user == class_obj.course.instructor
    

# Session views

class SessionListView(LoginRequiredMixin, ListView):
    model = Session
    template_name = 'courses/session_list.html'
    context_object_name = 'sessions'
    
    def get_queryset(self):
        classroom_id = self.kwargs["classroom_id"]
        return Session.objects.filter(classroom_id=classroom_id)
    

class SessionDetailView(LoginRequiredMixin, DetailView):
    model = Session
    template_name = 'courses/session_detail.html'
    context_object_name = 'session'
    
class SessionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Session
    form_class = SessionForm
    template_name = 'courses/session_form.html'

    def form_valid(self, form):
        form
        classroom = Classroom.objects.get(id=self.kwargs["classroom_id"])
        form.instance.classroom = classroom
        return super().form_valid(form)
    
    def test_func(self):
        classroom = Classroom.objects.get(id=self.kwargs["classroom_id"])
        return self.request.user == classroom.course.instructor

class SessionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Session
    form_class = SessionForm
    template_name = "courses/session_form.html"

    def test_func(self):
        session = self.get_object()
        return self.request.user == session.classroom.course.instructor

class SessionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Session
    template_name = "courses/session_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("session_list", kwargs={"classroom_id": self.object.classroom.id})

    def test_func(self):
        session = self.get_object()
        return self.request.user == session.classroom.course.instructor