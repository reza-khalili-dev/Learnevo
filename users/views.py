from pyexpat.errors import messages
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView, CreateView, ListView, DetailView, UpdateView 
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from books import models
from .mixins import RoleRequiredMixin
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from .models import Profile
from django.shortcuts import get_object_or_404
from .forms import UserRegisterForm 
from django import forms

from django.contrib.auth import get_user_model
User = get_user_model()

try:
    from courses.models import Course, Classroom
except Exception:
    Course = None
    Classroom = None

try:
    from books.models import Book
except Exception:
    Book = None

try:
    from orders.models import Order
except Exception:
    Order = None

try:
    from exams.models import Exam, Question
except Exception:
    Exam = None
    Question = None

try:
    from grades.models import Grade
except Exception:
    Grade = None



#Create your views here.


User = get_user_model()


class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    template_name = "users/user_form.html"
    fields = ["first_name", "last_name", "email", "phone_number", "role", "password"]
    success_url = reverse_lazy("users:user_list")

    def form_valid(self, form):
        messages.success(self.request, "User created successfully!")
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.role in ["manager", "employee"]

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def test_func(self):
        return getattr(self.request.user, "role", None) in ["manager", "employee"]


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    
    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')        
        if next_url:
            return next_url
        
        user = self.request.user
        role = getattr(user, 'role', None)

        if role == 'student':
            return reverse('users:student-dashboard')
        if role == 'instructor':
            return reverse('users:instructor-dashboard')
        if role in ('manager', 'employee'):
            return reverse('users:admin-dashboard')
        
        return super().get_success_url()  
    
class HomePageView(TemplateView):
    template_name = 'users/home.html'

class StudentDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = 'student'
    template_name = 'users/dashboards/student.html'

class InstructorDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = 'instructor'
    template_name = 'users/dashboards/instructor.html'

class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):

    template_name = "users/dashboards/admin.html"

    def test_func(self):
        return getattr(self.request.user, "role", None) in ["manager", "employee"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["user_count"] = User.objects.count()
        ctx["student_count"] = User.objects.filter(role="student").count()
        ctx["instructor_count"] = User.objects.filter(role="instructor").count()
        ctx["manager_count"] = User.objects.filter(role="manager").count()

        ctx["course_count"] = Course.objects.count() if Course is not None else 0
        ctx["book_count"] = Book.objects.count() if Book is not None else 0
        ctx["order_count"] = Order.objects.count() if Order is not None else 0
        ctx["exam_count"] = Exam.objects.count() if Exam is not None else 0

        ctx["roles_pie"] = {
            "students": ctx["student_count"],
            "instructors": ctx["instructor_count"],
            "managers": ctx["manager_count"],
        }

        now = timezone.now()
        monthly = []
        labels = []
        for i in range(5, -1, -1): 
            start = (now.replace(day=1) - timezone.timedelta(days=30*i)).replace(day=1)
            end = (start + timezone.timedelta(days=31)).replace(day=1)
            count = User.objects.filter(date_joined__gte=start, date_joined__lt=end).count()
            monthly.append(count)
            labels.append(start.strftime("%b %Y"))
        ctx["monthly_labels"] = labels
        ctx["monthly_data"] = monthly

        ctx["recent_users"] = User.objects.order_by("-date_joined")[:8]
        ctx["recent_instructors"] = User.objects.filter(role="instructor").order_by("-date_joined")[:8]

        classes = []
        if Classroom is not None:
            classrooms = Classroom.objects.all().order_by("-id")[:6]
            for cl in classrooms:
                cl_info = {
                    "id": cl.id,
                    "title": getattr(cl, "title", str(cl)),
                    "students_count": getattr(cl, "students", []).count() if hasattr(cl, "students") else 0,
                    "avg_grade": None,
                }
                if Grade is not None:
                    try:
                        g_qs = Grade.objects.filter(exam__course__classes=cl) 
                        avg = g_qs.aggregate_avg = g_qs.aggregate(models.Avg("score")).get("score__avg")
                        cl_info["avg_grade"] = round(avg, 2) if avg else None
                    except Exception:
                        cl_info["avg_grade"] = None
                classes.append(cl_info)
        ctx["classes"] = classes

        ctx["roles_pie_labels"] = list(ctx["roles_pie"].keys())
        ctx["roles_pie_values"] = list(ctx["roles_pie"].values())

        return ctx


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["image", "bio"]

class ProfileView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = "users/profile_detail.html"
    context_object_name = "profile"

    def get_object(self):
        user = self.request.user
        profile_id = self.kwargs.get("pk")

        if user.role == "manager" and profile_id:
            return get_object_or_404(Profile, pk=profile_id)

        if user.role == "employee" and profile_id:
            return get_object_or_404(Profile, pk=profile_id, user__role="student")
        return user.profile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile = ctx["profile"]

        if Course:
            ctx["enrolled_courses"] = getattr(profile.user, "enrolled_courses", Course.objects.none())
        if Grade and hasattr(profile.user, "results"):
            ctx["grades"] = profile.user.results.all()
        return ctx

class ProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Profile
    form_class = ProfileEditForm
    template_name = "users/profile_edit.html"

    def test_func(self):
        user = self.request.user
        profile = self.get_object()

        if user.role == "manager":
            return True
        if user.role == "employee" and profile.user.role == "student":
            return True
        return profile.user == user

    def get_success_url(self):
        messages.success(self.request, "Profile updated successfully ✅")
        return reverse_lazy("users:profile_detail", kwargs={"pk": self.object.pk})
