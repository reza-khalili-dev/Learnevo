from django.contrib import admin
from .models import Course , Classroom , Session , Attendance, Assignment, Submission
from users.models import CustomUser


# Register your models here.

class CourseAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "instructor":
            kwargs["queryset"] = CustomUser.objects.filter(role="instructor")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Course, CourseAdmin)

@admin.register(Classroom)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'start_date', 'end_date')
    list_filter = ('course', 'start_date')
    search_fields = ('title', 'course__title')

    filter_horizontal = ('students',)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "students":
            kwargs["queryset"] = CustomUser.objects.filter(role="student")
        return super().formfield_for_manytomany(db_field, request, **kwargs)



class SessionAdmin(admin.ModelAdmin):
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "students":
            kwargs["queryset"] = CustomUser.objects.filter(role="student")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

admin.site.register(Session, SessionAdmin)

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