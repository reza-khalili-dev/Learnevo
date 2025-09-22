from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin , UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from config import settings
from django.utils import timezone 
from .models import Course, Classroom, Session, Attendance, Assignment, Submission
from .forms import SessionForm, AttendanceForm, AssignmentForm, SubmissionForm



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
    
class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = "courses/attendance_list.html"
    context_object_name = "attendances"

    def get_queryset(self):
        session_pk = self.kwargs.get("session_pk")
        qs = Attendance.objects.filter(session_id=session_pk).select_related("student", "marked_by")
        if getattr(self.request.user, "role", None) == "Student":
            qs = qs.filter(student=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["session"] = get_object_or_404(Session, pk=self.kwargs.get("session_pk"))
        ctx["enrolled_students"] = ctx["session"].classroom.students.all()
        return ctx
    
# Attendance Views
class AttendanceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = "courses/attendance_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(Session, pk=kwargs.get("session_pk"))
        self.student = get_object_or_404(settings.AUTH_USER_MODEL, pk=kwargs.get("student_pk"))
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        user = self.request.user
        if getattr(user, "role", None) in ("manager", "employee"):
            return True
        return user == self.session.classroom.course.instructor

    def form_valid(self, form):
        form.instance.session = self.session
        form.instance.student = self.student
        form.instance.marked_by = self.request.user
        form.instance.full_clean()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("attendance_list", kwargs={"session_pk": self.session.pk})


class AttendanceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = "courses/attendance_form.html"

    def test_func(self):
        attendance = self.get_object()
        user = self.request.user
        if getattr(user, "role", None) in ("manager", "employee"):
            return True
        return user == attendance.session.classroom.course.instructor

    def form_valid(self, form):
        form.instance.marked_by = self.request.user
        form.instance.full_clean()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("attendance_list", kwargs={"session_pk": self.object.session.pk})


class AttendanceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Attendance
    template_name = "courses/attendance_confirm_delete.html"

    def test_func(self):
        attendance = self.get_object()
        user = self.request.user
        if getattr(user, "role", None) in ("manager", "employee"):
            return True
        return user == attendance.session.classroom.course.instructor

    def get_success_url(self):
        return reverse_lazy("attendance_list", kwargs={"session_pk": self.object.session.pk})


# Assignment views
class AssignmentListView(LoginRequiredMixin, ListView):
    model = Assignment 
    template_name = "courses/assignment_list.html" 
    context_object_name = "assignments"  

    def get_queryset(self):
        course_pk = self.kwargs.get("course_pk")
        qs = Assignment.objects.filter(course__pk=course_pk, is_published=True).order_by("-created_at")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["course"] = get_object_or_404(Course, pk=self.kwargs.get("course_pk"))
        return ctx

class AssignmentDetailView(LoginRequiredMixin, DetailView):
    model = Assignment
    template_name = "courses/assignment_detail.html"
    context_object_name = "assignment"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        assignment = self.get_object()
        user = self.request.user
        if user == assignment.course.instructor or getattr(user, "role", None) in ("manager", "employee"):
            ctx["submissions"] = assignment.submissions.select_related("student").all()
        else:
            ctx["submissions"] = assignment.submissions.filter(student=user)
        return ctx

class AssignmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = "courses/assignment_form.html"

    def form_valid(self, form):
        course = get_object_or_404(Course, pk=self.kwargs.get("course_pk"))
        form.instance.course = course
        return super().form_valid(form)

    def test_func(self):
        course = get_object_or_404(Course, pk=self.kwargs.get("course_pk"))
        return self.request.user == course.instructor

    def get_success_url(self):
        return reverse("assignment_detail", kwargs={"pk": self.object.pk})

class AssignmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = "courses/assignment_form.html"

    def test_func(self):
        assignment = self.get_object()
        return self.request.user == assignment.course.instructor

    def get_success_url(self):
        return reverse("assignment_detail", kwargs={"pk": self.object.pk})

class AssignmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Assignment
    template_name = "courses/assignment_confirm_delete.html"

    def test_func(self):
        assignment = self.get_object()
        return self.request.user == assignment.course.instructor

    def get_success_url(self):
        return reverse_lazy("assignment_list", kwargs={"course_pk": self.object.course.pk})


# Submission views
class SubmissionCreateView(LoginRequiredMixin, CreateView):
    model = Submission
    form_class = SubmissionForm
    template_name = "courses/submission_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.assignment = get_object_or_404(Assignment, pk=kwargs.get("assignment_pk"))
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        user = self.request.user
        if getattr(user, "role", None) != "Student":
            return False
        classrooms = self.assignment.course.classes.all()
        enrolled = any(cl.students.filter(pk=user.pk).exists() for cl in classrooms)
        return enrolled

    def form_valid(self, form):
        if self.assignment.due_date and timezone.now() > self.assignment.due_date:
            form.add_error(None, "Deadline has passed. You cannot submit.")
            return self.form_invalid(form)

        form.instance.assignment = self.assignment
        form.instance.student = self.request.user
        form.instance.full_clean()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("assignment_detail", kwargs={"pk": self.assignment.pk})

class SubmissionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Submission
    form_class = SubmissionForm
    template_name = "courses/submission_form.html"

    def test_func(self):
        submission = self.get_object()
        user = self.request.user
        if getattr(user, "role", None) in ("manager", "employee"):
            return True
        if user == submission.student:
            if submission.assignment.due_date and timezone.now() > submission.assignment.due_date:
                return False
            return True
        return user == submission.assignment.course.instructor

    def form_valid(self, form):
        form.instance.full_clean()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("assignment_detail", kwargs={"pk": self.object.assignment.pk})

class SubmissionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Submission
    template_name = "courses/submission_list.html"
    context_object_name = "submissions"

    def test_func(self):
        assignment = get_object_or_404(Assignment, pk=self.kwargs.get("assignment_pk"))
        user = self.request.user
        return user == assignment.course.instructor or getattr(user, "role", None) in ("manager", "employee")

    def get_queryset(self):
        return Submission.objects.filter(assignment__pk=self.kwargs.get("assignment_pk")).select_related("student").order_by("-submitted_at")

