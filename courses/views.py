from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin , UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from config import settings
from django.utils import timezone 
from .models import Course, Classroom, Session, Attendance, Assignment, Submission
from .forms import SessionForm, AttendanceForm, AssignmentForm, SubmissionForm
from django.forms import modelformset_factory
from django.contrib import messages
from django.views import View


# Course views

class CoursesDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "courses/courses_dashboard.html"

    def test_func(self):
        return self.request.user.role in ["manager", "employee"] 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.all()
        return context

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
    template_name = "courses/course_form.html"
    success_url = reverse_lazy("courses:course_list")

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.role in ["manager", "employee"]

class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    fields = ["title", "description"]
    template_name = 'courses/course_form.html'

    def test_func(self):
        course = self.get_object()
        return (self.request.user.role in ["manager", "employee"] or self.request.user == course.instructor)

    def get_success_url(self):
        return reverse('courses:course_detail', kwargs={'pk': self.object.pk})

class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('courses:course_list')

    def test_func(self):
        course = self.get_object()
        return (
            self.request.user.role in ["manager", "employee"]
            or self.request.user == course.instructor
        )


# Classroom views

class ClassListView(LoginRequiredMixin, ListView):
    model = Classroom
    template_name = 'courses/class_list.html'
    context_object_name = 'classes'
    
class ClassDetailView(LoginRequiredMixin, DetailView):
    model = Classroom
    template_name = 'courses/class_detail.html'
    context_object_name = 'class_obj'

    def get_queryset(self):
        return Classroom.objects.prefetch_related('sessions', 'students', 'course')
    
class ClassCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Classroom
    fields = ['course', 'title', 'start_date', 'end_date', 'capacity']
    template_name = 'courses/class_form.html'

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        user_role = getattr(self.request.user, 'role', '').lower()

        if user_role == 'instructor':
            form.fields['course'].queryset = Course.objects.filter(instructor=self.request.user)
        elif user_role in ['manager', 'employee']:
            form.fields['course'].queryset = Course.objects.all()
        else:
            form.fields['course'].queryset = Course.objects.none()

        return form

    def test_func(self):
        return getattr(self.request.user, 'role', None) in ['instructor', 'manager', 'employee']
    
    def form_valid(self, form):
        course = form.cleaned_data.get('course')
        user = self.request.user
        # instructors can only create classes for their own courses
        if user.role == "instructor" and course.instructor != user:
            form.add_error('course', 'You can only create classes for your own courses.')
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('courses:class_detail', kwargs={'pk': self.object.pk})

    
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
    


# attendance views 

def role_of(user):
    try:
        return (user.role or '').lower()
    except Exception:
        return ''

class ClassAttendanceListView(LoginRequiredMixin, ListView):
    model = Classroom
    template_name = 'courses/attendance_class_list.html'
    context_object_name = 'classrooms'

    def get_queryset(self):
        user = self.request.user
        if role_of(user) in ('manager', 'employee'):
            return Classroom.objects.select_related('course', 'course__instructor').prefetch_related('students')

        if role_of(user) == 'instructor':
            return Classroom.objects.filter(course__instructor=user).select_related('course')

        return Classroom.objects.filter(students=user)

class ClassroomAttendanceView(LoginRequiredMixin, View):

    template_name = 'courses/classroom_attendance.html'

    def get(self, request, classroom_pk):
        classroom = get_object_or_404(Classroom.objects.select_related('course','course__instructor').prefetch_related('students','sessions'), pk=classroom_pk)
        session_pk = request.GET.get('session')
        session = None
        if session_pk:
            session = classroom.sessions.filter(pk=session_pk).first()
        else:
            session = classroom.sessions.order_by('-start_time').first()

        AttendanceFormSet = modelformset_factory(Attendance, form=AttendanceForm, extra=0)

        if session:
            existing_qs = Attendance.objects.filter(session=session).select_related('student','marked_by')
        else:
            existing_qs = Attendance.objects.none()

        attendance_map = {a.student_id: a for a in existing_qs}
        rows = []
        for student in classroom.students.all():
            rows.append({
                'student': student,
                'attendance': attendance_map.get(student.pk)
            })

        context = {
            'classroom': classroom,
            'instructor': classroom.course.instructor,
            'session': session,
            'sessions': classroom.sessions.all(),
            'rows': rows,
        }
        return render(request, self.template_name, context)

    def post(self, request, classroom_pk):

        classroom = get_object_or_404(Classroom.objects.prefetch_related('students','sessions').select_related('course'), pk=classroom_pk)
        session_pk = request.POST.get('session')
        session = None
        if session_pk:
            session = classroom.sessions.filter(pk=session_pk).first()
        else:
            messages.error(request, 'Session not specified.')
            return redirect('courses:attendance_class_list')

        user = request.user
        if not (role_of(user) in ('manager','employee') or user == classroom.course.instructor):
            messages.error(request, 'Permission denied.')
            return redirect('courses:attendance_class_list')

        updated = 0
        created = 0
        for student in classroom.students.all():
            sid = str(student.pk)
            status = request.POST.get(f'status_{sid}')
            note = request.POST.get(f'note_{sid}', '').strip() or None
            if status is None:
                continue
            if getattr(student, 'role', '').lower() != 'student':
                continue
            attendance_obj, created_flag = Attendance.objects.get_or_create(session=session, student=student, defaults={
                'status': status,
                'note': note,
                'marked_by': user
            })
            if not created_flag:
                # update
                attendance_obj.status = status
                attendance_obj.note = note
                attendance_obj.marked_by = user
                attendance_obj.save()
                updated += 1
            else:
                created += 1
        messages.success(request, f'Attendance updated: {updated}, created: {created}')
        return redirect('courses:classroom_attendance', classroom_pk=classroom.pk)

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
        return self.request.user == classroom.course.instructor or self.request.user.role in ["manager", "employee"]



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


class InstructorCourseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Course
    template_name = "courses/instructor_courses.html"
    context_object_name = "courses"

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)

    def test_func(self):
        return self.request.user.role == "Instructor"

class InstructorSessionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Session
    template_name = "courses/instructor_sessions.html"
    context_object_name = "sessions"

    def get_queryset(self):
        return Session.objects.filter(course__instructor=self.request.user)

    def test_func(self):
        return self.request.user.role == "Instructor"