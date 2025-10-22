from pyexpat.errors import messages
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from books import models
from .mixins import RoleRequiredMixin
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone

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
            return reverse('student-dashboard')
        if role == 'instructor':
            return reverse('instructor-dashboard')
        if role in ('manager', 'employee'):
            return reverse('admin-dashboard')
        
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
    """
    داشبورد ادمین: آمار کلی + نمودارها + لیست‌های سریع
    دسترسی: فقط نقش manager یا employee
    """
    template_name = "users/dashboards/admin.html"

    # اجازه: فقط manager یا employee می‌توانند وارد شوند
    def test_func(self):
        return getattr(self.request.user, "role", None) in ["manager", "employee"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # ====== آمار کلی ======
        ctx["user_count"] = User.objects.count()
        # شمارش نقش‌ها (Students / Instructors / Admins)
        ctx["student_count"] = User.objects.filter(role="student").count()
        ctx["instructor_count"] = User.objects.filter(role="instructor").count()
        ctx["manager_count"] = User.objects.filter(role="manager").count()

        ctx["course_count"] = Course.objects.count() if Course is not None else 0
        ctx["book_count"] = Book.objects.count() if Book is not None else 0
        ctx["order_count"] = Order.objects.count() if Order is not None else 0
        ctx["exam_count"] = Exam.objects.count() if Exam is not None else 0

        # ====== داده‌های نمودار ======
        # Pie: نقش کاربران
        ctx["roles_pie"] = {
            "students": ctx["student_count"],
            "instructors": ctx["instructor_count"],
            "managers": ctx["manager_count"],
        }

        # Line: growth (نمونه‌ای از 6 ماه اخیر بر اساس ثبت‌نام‌ها)
        # اینجا آمار ماهانه ساده‌سازی شده است
        now = timezone.now()
        monthly = []
        labels = []
        for i in range(5, -1, -1):  # 6 ماه اخیر
            start = (now.replace(day=1) - timezone.timedelta(days=30*i)).replace(day=1)
            end = (start + timezone.timedelta(days=31)).replace(day=1)
            count = User.objects.filter(date_joined__gte=start, date_joined__lt=end).count()
            monthly.append(count)
            labels.append(start.strftime("%b %Y"))
        ctx["monthly_labels"] = labels
        ctx["monthly_data"] = monthly

        # ====== لیست‌های سریع برای جدول‌ها ======
        ctx["recent_users"] = User.objects.order_by("-date_joined")[:8]
        ctx["recent_instructors"] = User.objects.filter(role="instructor").order_by("-date_joined")[:8]

        # ====== اطلاعات کلاس‌ها و میانگین نمرات (اگر مدل Grade موجود باشد) ======
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
                # تلاش برای محاسبه میانگین نمره‌ی دانشجویان در آن کلاس (اگر Grade موجود)
                if Grade is not None:
                    # سعی می‌کنیم نمره‌های مربوط به امتحانات/assignments آن کلاس را محاسبه کنیم
                    try:
                        # این بخش ممکن است نیاز به هماهنگی با مدل Grade شما داشته باشد
                        g_qs = Grade.objects.filter(exam__course__classes=cl)  # فرض ساختار
                        avg = g_qs.aggregate_avg = g_qs.aggregate(models.Avg("score")).get("score__avg")
                        cl_info["avg_grade"] = round(avg, 2) if avg else None
                    except Exception:
                        cl_info["avg_grade"] = None
                classes.append(cl_info)
        ctx["classes"] = classes

        # ====== نمودار نقش‌ها بصورت کلید/مقدار (قابل استفاده در Chart.js) ======
        ctx["roles_pie_labels"] = list(ctx["roles_pie"].keys())
        ctx["roles_pie_values"] = list(ctx["roles_pie"].values())

        return ctx