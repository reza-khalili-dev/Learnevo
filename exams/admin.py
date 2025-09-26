from django.contrib import admin
from .models import Exam, Question, Choice, StudentAnswer, ExamResult



# Register your models here.


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2
    
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "start_time", "end_time", "duration")
    search_fields = ("title", "description", "instructor__email")
    list_filter = ("instructor", "start_time", "end_time")
    inlines = [QuestionInline]
    
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "exam", "points")
    search_fields = ("text", "exam__title")
    list_filter = ("exam",)
    inlines = [QuestionInline]

admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ("student", "question", "choice", "submitted_at")
    search_fields = ("student__email", "question__text")
    list_filter = ("submitted_at", "question__exam")

admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ("student", "exam", "score", "is_approved", "created_at")
    search_fields = ("student__email", "exam__title")
    list_filter = ("is_approved", "exam")
    