from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin , UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
from config import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone 
from .models import Course, Classroom, Session, Attendance, Assignment, Submission
from .forms import ClassForm, SessionForm, AttendanceForm, AssignmentForm, SubmissionForm
from django.forms import modelformset_factory
from django.contrib import messages
from django.views import View
from .utils.pdf_utils import generate_pdf_response



# Course views

class CoursesDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "courses/courses_dashboard.html"

    def test_func(self):
        return self.request.user.role in ["manager", "employee"] 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses_count'] = Course.objects.count()
        context['classes_count'] = Classroom.objects.count()
        context['sessions_count'] = Session.objects.count()
        
        from django.db.models import Count
        unique_students = Classroom.objects.aggregate(
            total_students=Count('students', distinct=True)
        )
        context['students_count'] = unique_students['total_students']
        
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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        classroom = self.get_object()

        ctx["sessions"] = Session.objects.filter(classroom=classroom).order_by("start_time")
        session_ids_with_attendance = Attendance.objects.filter(session__classroom=classroom).values_list("session_id", flat=True)
        for s in ctx["sessions"]:
            s.has_attendance = s.id in session_ids_with_attendance
    
        students_qs = classroom.students.all()
        ctx["students"] = students_qs
        ctx["assignments"] = Assignment.objects.filter(course=classroom.course).order_by("-created_at")
        ctx["submissions"] = Submission.objects.filter(
            assignment__course=classroom.course
        ).select_related("student", "assignment").order_by("-submitted_at")[:20]


        ctx["attendances"] = Attendance.objects.filter(
            session__classroom=classroom
        ).select_related('session', 'student', 'marked_by').order_by('-session__start_time')

        session_id = self.request.GET.get('session_id') or self.request.GET.get('session') 
        selected_session = None
        attendance_rows = []  
        if session_id:
            selected_session = Session.objects.filter(pk=session_id, classroom=classroom).first()
            if selected_session:
                existing_qs = Attendance.objects.filter(session=selected_session).select_related('student')
                existing_map = {a.student_id: a for a in existing_qs}
                for student in students_qs:
                    attendance_rows.append({
                        'student': student,
                        'attendance': existing_map.get(student.pk) 
                    })

        ctx['selected_session'] = selected_session
        ctx['attendance_rows'] = attendance_rows
        
        

        return ctx

    
class ClassCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Classroom
    form_class = ClassForm
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
        return getattr(self.request.user, 'role', None) in ['manager', 'employee']
    
    def form_valid(self, form):
        course = form.cleaned_data.get('course')
        user = self.request.user
        if user.role == "instructor" and course.instructor != user:
            form.add_error('course', 'You can only create classes for your own courses.')
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("courses:class_detail", kwargs={"pk": self.object.pk})

    
class ClassUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Classroom
    form_class = ClassForm
    template_name = 'courses/class_form.html'

    def test_func(self):
        user = self.request.user
        return user.role in ['manager', 'employee']

    def get_success_url(self):
        return reverse("courses:class_detail", kwargs={"pk": self.object.pk})


class ClassDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Classroom
    template_name = 'courses/class_confirm_delete.html'
    success_url = reverse_lazy('courses:class_list')

    def test_func(self):
        user = self.request.user
        return user.role in ['manager', 'employee']
    


# attendance views 

def role_of(user):
    try:
        return (user.role or '').lower()
    except Exception:
        return ''




class ClassroomAttendanceView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "courses/class_detail.html"

    def test_func(self):
        user = self.request.user
        classroom = get_object_or_404(Classroom, pk=self.kwargs["classroom_pk"])
        return (
            user.role in ['manager', 'employee'] or 
            user == classroom.instructor
        )

    def get(self, request, classroom_pk):
        classroom = get_object_or_404(Classroom, pk=classroom_pk)

        context = {
            "class_obj": classroom,
            "sessions": Session.objects.filter(classroom=classroom).order_by("start_time"),
            "students": classroom.students.all(),
            "assignments": Assignment.objects.filter(course=classroom.course).order_by("-created_at"),
            "attendances": Attendance.objects.filter(
                session__classroom=classroom
            ).select_related('session', 'student', 'marked_by').order_by('-session__start_time'),
            "submissions": Submission.objects.filter(
                assignment__course=classroom.course
            ).select_related("student", "assignment").order_by("-submitted_at")[:20]
        }

        return render(request, self.template_name, context)

    def post(self, request, classroom_pk):
        classroom = get_object_or_404(Classroom, pk=classroom_pk)

        session_id = request.POST.get("session_id")
        student_id = request.POST.get("student_id")
        status = request.POST.get("status")

        if session_id and student_id:
            Attendance.objects.update_or_create(
                session_id=session_id,
                student_id=student_id,
                defaults={
                    "status": status,
                    "marked_by": request.user
                }
            )

        return redirect("courses:classroom_attendance", classroom_pk=classroom.pk)


class AttendanceSaveView(LoginRequiredMixin, View):
    def post(self, request, classroom_pk):
        classroom = get_object_or_404(Classroom, pk=classroom_pk)

        session_id = request.POST.get("session_id")
        session = get_object_or_404(Session, id=session_id, classroom=classroom)

        for student in classroom.students.all():
            field = f"status_{student.id}"
            status = request.POST.get(field)

            if status:
                Attendance.objects.update_or_create(
                    session=session,
                    student=student,
                    defaults={
                        "status": status,
                        "marked_by": request.user,
                    },
                )

        return redirect(f"/courses/classes/{classroom.pk}/?session_id={session.id}#attendance")


# Session views



class SessionDetailView(LoginRequiredMixin, DetailView):
    model = Session
    template_name = 'courses/session_detail.html'
    context_object_name = 'session'

    
class SessionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Session
    form_class = SessionForm
    template_name = 'courses/session_form.html'

    def form_valid(self, form):
        classroom = Classroom.objects.get(id=self.kwargs["classroom_id"])
        self.object = form.save(commit=False)
        self.object.classroom = classroom
        self.object.save()
        return redirect(self.get_success_url())

    # redirect to the classroom detail (hub)
    def get_success_url(self):
        return reverse('courses:class_detail', kwargs={"pk": self.object.classroom.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classroom_id'] = self.kwargs['classroom_id']
        return context

    def test_func(self):
        return self.request.user.role in ['manager', 'employee']




class SessionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Session
    form_class = SessionForm
    template_name = "courses/session_form.html"

    def get_success_url(self):
        return reverse('courses:class_detail', kwargs={"pk": self.object.classroom.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classroom_id'] = self.object.classroom.id
        return context

    def test_func(self):
        return self.request.user.role in ['manager', 'employee']


    
    
class SessionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Session
    template_name = "courses/session_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("courses:class_detail", kwargs={"pk": self.object.classroom.id})

    def test_func(self):
        user = self.request.user
        if user.role in ['manager', 'employee']:
            return True
        return False
    


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
        

        is_instructor_of_course = assignment.course.classes.filter(instructor=user).exists()
        has_instructor_access = user.role in ["manager", "employee", "instructor"] and is_instructor_of_course
        

        if has_instructor_access:
            ctx["submissions"] = assignment.submissions.select_related("student").all()
            ctx["user_submissions"] = None
        else:
            ctx["user_submissions"] = assignment.submissions.filter(student=user)
            ctx["submissions"] = None
            

        ctx["has_instructor_access"] = has_instructor_access
        ctx["is_instructor_of_course"] = is_instructor_of_course
        ctx["classrooms"] = assignment.course.classes.all()
        
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
        user = self.request.user
        
        if user.role in ["manager", "employee"]:
            return True
            
        if user.role == "instructor":
            return course.classes.filter(instructor=user).exists()
            
        return False

    def get_success_url(self):
        classroom = self.object.course.classes.first()
        if classroom:
            return reverse("courses:class_detail", kwargs={"pk": classroom.pk}) + "#assignments"
        return reverse("courses:course_detail", kwargs={"pk": self.object.course.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = get_object_or_404(Course, pk=self.kwargs.get("course_pk"))
        context['classroom'] = course.classes.first()
        return context

class AssignmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = "courses/assignment_form.html"

    def test_func(self):
        assignment = self.get_object()
        user = self.request.user
        
        if user.role in ["manager", "employee"]:
            return True
            
        if user.role == "instructor":
            return assignment.course.classes.filter(instructor=user).exists()
            
        return False

    def get_success_url(self):
        classroom = self.object.course.classes.first()
        if classroom:
            return reverse("courses:class_detail", kwargs={"pk": classroom.pk}) + "#assignments"
        return reverse("courses:assignment_detail", kwargs={"pk": self.object.pk})


class AssignmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Assignment
    template_name = "courses/assignment_confirm_delete.html"

    def test_func(self):
        assignment = self.get_object()
        user = self.request.user
        
        if user.role in ["manager", "employee"]:
            return True
            
        if user.role == "instructor":
            return assignment.course.classes.filter(instructor=user).exists()
            
        return False

    def get_success_url(self):

        classroom = self.object.course.classes.first()
        if classroom:
            return reverse("courses:class_detail", kwargs={"pk": classroom.pk}) + "#assignments"
        else:
            return reverse("courses:course_detail", kwargs={"pk": self.object.course.pk})


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



# Reports Views



class ReportsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "courses/reports/reports_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        user = self.request.user
        if user.role not in ["manager", "employee"]:
            raise PermissionDenied("You do not have access to reports.")

        ctx["classes"] = Classroom.objects.all().order_by("-start_date")
        return ctx
    
    
class ReportClassView(LoginRequiredMixin, TemplateView):
    template_name = "courses/reports/report_class.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        class_id = kwargs["class_id"]

        classroom = Classroom.objects.get(pk=class_id)
        ctx["classroom"] = classroom

        sessions = Session.objects.filter(classroom=classroom).order_by("start_time")
        ctx["sessions"] = sessions

        students = classroom.students.all().order_by("first_name")

        rows = []
        attendance_qs = Attendance.objects.filter(session__in=sessions)

        attendance_map = {
            (a.student_id, a.session_id): a.status
            for a in attendance_qs
        }


        present_count = 0
        late_count = 0
        excused_count = 0
        absent_count = 0

        for student in students:
            row = {
                "student": student,
                "statuses": []
            }

            for session in sessions:
                status = attendance_map.get((student.id, session.id), "absent")
                row["statuses"].append(status)
                
                if status == "present":
                    present_count += 1
                elif status == "late":
                    late_count += 1
                elif status == "excused":
                    excused_count += 1
                else:
                    absent_count += 1

            rows.append(row)

        ctx["rows"] = rows
        ctx["present_count"] = present_count
        ctx["late_count"] = late_count
        ctx["excused_count"] = excused_count
        ctx["absent_count"] = absent_count
        ctx["total_attendance"] = present_count + late_count  
        
        ctx["pdf_url"] = f"/reports/class/{class_id}/pdf/"
        
        return ctx

class ReportClassPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        class_id = kwargs["class_id"]
        
        if request.user.role not in ["manager", "employee"]:
            raise PermissionDenied("You do not have access to reports.")
        
        classroom = Classroom.objects.get(pk=class_id)
        sessions = Session.objects.filter(classroom=classroom).order_by("start_time")
        students = classroom.students.all().order_by("first_name")

        rows = []
        attendance_qs = Attendance.objects.filter(session__in=sessions)

        attendance_map = {
            (a.student_id, a.session_id): a.status
            for a in attendance_qs
        }

        present_count = 0
        late_count = 0
        excused_count = 0
        absent_count = 0

        for student in students:
            row = {
                "student": student,
                "statuses": []
            }

            for session in sessions:
                status = attendance_map.get((student.id, session.id), "absent")
                row["statuses"].append(status)
                
                if status == "present":
                    present_count += 1
                elif status == "late":
                    late_count += 1
                elif status == "excused":
                    excused_count += 1
                else:
                    absent_count += 1

            rows.append(row)

        context = {
            "classroom": classroom,
            "sessions": sessions,
            "rows": rows,
            "present_count": present_count,
            "late_count": late_count,
            "excused_count": excused_count,
            "absent_count": absent_count,
            "total_attendance": present_count + late_count,
            "generated_date": timezone.now()
        }

        filename = f"attendance_report_{classroom.title.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d')}"
        return generate_pdf_response("courses/reports/report_class_pdf.html", context, filename)
    
    
class ReportSessionView(LoginRequiredMixin, TemplateView):
    template_name = "courses/reports/report_session.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        session_id = kwargs["session_id"]

        session = Session.objects.get(pk=session_id)
        classroom = session.classroom

        ctx["session"] = session
        ctx["classroom"] = classroom

        students = classroom.students.all().order_by("first_name")
        
        attendance_qs = Attendance.objects.filter(session=session)

        attendance_map = {
            a.student_id: a.status
            for a in attendance_qs
        }

        rows = []
        present_count = 0
        late_count = 0
        excused_count = 0
        absent_count = 0
        
        for student in students:
            status = attendance_map.get(student.id, "absent")
            rows.append({
                "student": student,
                "status": status
            })
            
            if status == "present":
                present_count += 1
            elif status == "late":
                late_count += 1
            elif status == "excused":
                excused_count += 1
            else:
                absent_count += 1

        ctx["rows"] = rows
        ctx["present_count"] = present_count
        ctx["late_count"] = late_count
        ctx["excused_count"] = excused_count
        ctx["absent_count"] = absent_count
        ctx["attendance_rate"] = round(((present_count + late_count) / len(rows)) * 100, 2) if rows else 0
        
        ctx["pdf_url"] = f"/reports/session/{session_id}/pdf/"
        
        return ctx

class ReportSessionPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        session_id = kwargs["session_id"]
        
        if request.user.role not in ["manager", "employee"]:
            raise PermissionDenied("You do not have access to reports.")
        
        session = Session.objects.get(pk=session_id)
        classroom = session.classroom
        students = classroom.students.all().order_by("first_name")
        
        attendance_qs = Attendance.objects.filter(session=session)
        attendance_map = {
            a.student_id: a.status
            for a in attendance_qs
        }

        rows = []
        present_count = 0
        late_count = 0
        excused_count = 0
        absent_count = 0
        
        for student in students:
            status = attendance_map.get(student.id, "absent")
            rows.append({
                "student": student,
                "status": status
            })
            
            if status == "present":
                present_count += 1
            elif status == "late":
                late_count += 1
            elif status == "excused":
                excused_count += 1
            else:
                absent_count += 1

        context = {
            "session": session,
            "classroom": classroom,
            "rows": rows,
            "present_count": present_count,
            "late_count": late_count,
            "excused_count": excused_count,
            "absent_count": absent_count,
            "attendance_rate": round(((present_count + late_count) / len(rows)) * 100, 2) if rows else 0,
            "generated_date": timezone.now()
        }

        filename = f"session_attendance_{session.start_time.strftime('%Y%m%d')}_{classroom.title.replace(' ', '_')}"
        return generate_pdf_response("courses/reports/report_session_pdf.html", context, filename)



class StudentListPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        class_id = kwargs["class_id"]
        
        # Check permissions
        if request.user.role not in ["manager", "employee", "instructor"]:
            raise PermissionDenied("You do not have access to student lists.")
        
        classroom = Classroom.objects.get(pk=class_id)
        
        # Check if user is instructor of this class
        if request.user.role == "instructor" and classroom.instructor != request.user:
            raise PermissionDenied("You can only export student lists for your own classes.")
        
        students = classroom.students.all().select_related('profile').order_by('first_name', 'last_name')
        
        # Calculate available seats
        student_count = students.count()
        capacity = classroom.capacity or 0
        available_seats = capacity - student_count if capacity > 0 else None
        enrollment_rate = (student_count / capacity * 100) if capacity > 0 else None

        context = {
            "classroom": classroom,
            "students": students,
            "student_count": student_count,
            "available_seats": available_seats,
            "enrollment_rate": enrollment_rate,
            "generated_date": timezone.now()
        }

        filename = f"student_list_{classroom.title.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d')}"
        return generate_pdf_response("courses/reports/student_list_pdf.html", context, filename)