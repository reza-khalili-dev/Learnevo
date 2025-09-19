from django.contrib import admin
from .models import Course , Classroom , Session


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