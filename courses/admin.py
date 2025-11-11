from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from .models import Course, Classroom, Session, Attendance, Assignment, Submission
from users.models import CustomUser

# ----------------------------
# Session Inline برای نمایش در Classroom
# ----------------------------
class SessionInline(admin.TabularInline):
    model = Session
    extra = 0
    fields = ('title', 'start_time', 'end_time')

# ----------------------------
# Attendance Inline برای نمایش در Session
# ----------------------------
class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    fields = ("student", "status", "note", "marked_by", "marked_at")
    readonly_fields = ("marked_by", "marked_at")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        if obj:  # وقتی Session موجود است
            class _AttendanceForm(forms.ModelForm):
                class Meta:
                    model = Attendance
                    fields = "__all__"
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    # فقط دانش‌آموزان کلاس مربوطه
                    self.fields["student"].queryset = obj.classroom.students.all()

            formset.form = _AttendanceForm
        return formset

# ----------------------------
# Course Admin
# ----------------------------
class CourseAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "instructor":
            kwargs["queryset"] = CustomUser.objects.filter(role="instructor")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Course, CourseAdmin)

# ----------------------------
# Classroom Admin
# ----------------------------
@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'start_date', 'end_date')
    list_filter = ('course', 'start_date')
    search_fields = ('title', 'course__title')
    filter_horizontal = ('students',)
    inlines = [SessionInline]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "students":
            kwargs["queryset"] = CustomUser.objects.filter(role="student")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

# ----------------------------
# Session Admin
# ----------------------------
@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("title", "classroom", "start_time", "end_time", "created_at")
    list_filter = ("classroom", "start_time")
    search_fields = ("title", "classroom__title")
    readonly_fields = ("created_at", "updated_at")
    inlines = [AttendanceInline]

# ----------------------------
# Attendance Admin (Updated)
# ----------------------------
def role_of(user):
    """تبدیل نقش به lowercase برای مقایسه امن"""
    try:
        return (user.role or '').lower()
    except Exception:
        return ''


class AttendanceAdminForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # فیلتر دانش‌آموزان فقط از کلاس مرتبط
        if self.instance and self.instance.pk:
            classroom = self.instance.session.classroom
            self.fields["student"].queryset = classroom.students.all()
            self.fields["session"].queryset = classroom.sessions.all()
        else:
            self.fields["student"].queryset = CustomUser.objects.filter(role="student")
            self.fields["session"].queryset = Session.objects.all()


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    form = AttendanceAdminForm
    list_display = ("student", "session", "status", "note", "marked_by", "marked_at")
    list_filter = ("session__classroom", "session", "status")
    search_fields = (
        "student__first_name", "student__last_name", "student__email", "session__title"
    )
    readonly_fields = ("marked_by", "marked_at")

    def save_model(self, request, obj, form, change):
        """وقتی حضور ثبت میشه، کاربر فعلی رو به عنوان marked_by ذخیره کن"""
        if not obj.marked_by_id:
            obj.marked_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """مدیرها و کارمندان همه حضورها رو می‌بینن، مدرس فقط کلاس‌های خودش"""
        qs = super().get_queryset(request)
        user = request.user
        user_role = role_of(user)

        if user_role in ("manager", "employee"):
            return qs
        if user_role == "instructor":
            return qs.filter(session__classroom__course__instructor=user)
        return qs.none()  # سایر نقش‌ها نمی‌بینن




# ----------------------------
# Assignment Admin
# ----------------------------
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "session", "due_date", "max_score", "is_published")
    list_filter = ("course", "is_published")
    search_fields = ("title", "description")
    raw_id_fields = ("course", "session")

# ----------------------------
# Submission Admin
# ----------------------------
@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "submitted_at", "grade", "graded_by")
    list_filter = ("assignment__course",)
    search_fields = ("student__email", "student__first_name", "student__last_name", "assignment__title")
    readonly_fields = ("submitted_at", "graded_at")
