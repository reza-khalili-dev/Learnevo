from django.contrib import admin
from .models import Course , Class

# Register your models here.

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "created_at", "updated_at")
    search_fields = ("title", "description")
    list_filter = ("created_at", "instructor")

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'start_date', 'end_date')
    list_filter = ('course', 'start_date')
    search_fields = ('title', 'course__title')