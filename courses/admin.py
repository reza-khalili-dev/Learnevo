from django.contrib import admin
from .models import Course , Classroom , Session , Attendance, Assignment, Submission


# Register your models here.

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "created_at", "updated_at")
    search_fields = ("title", "description")
    list_filter = ("created_at", "instructor")

@admin.register(Classroom)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'start_date', 'end_date')
    list_filter = ('course', 'start_date')
    search_fields = ('title', 'course__title')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'classroom', 'start_time', 'end_time')
    list_filter = ('classroom', 'start_time')
    search_fields = ('title', 'description')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("session", "student", "status", "marked_by", "marked_at")
    list_filter = ("status", "session__classroom__course")
    search_fields = ("student__first_name", "student__last_name", "student__email", "session__title")
    readonly_fields = ("marked_at",)
    

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "session", "due_date", "max_score", "is_published")
    list_filter = ("course", "is_published")
    search_fields = ("title", "description")
    raw_id_fields = ("course", "session") 

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "submitted_at", "grade", "graded_by")
    list_filter = ("assignment__course",)
    search_fields = ("student__email", "student__first_name", "student__last_name", "assignment__title")
    readonly_fields = ("submitted_at", "graded_at")