from django.contrib import admin
from .models import Exam, Question, Choice, StudentAnswer, ExamResult

# --- Inline definitions ---

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


# --- Exam admin ---
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "start_time", "end_time", "duration")
    list_filter = ("instructor", "start_time")
    search_fields = ("title", "description")
    inlines = [QuestionInline]


# --- Question admin ---
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "exam", "qtype", "points")
    list_filter = ("exam", "qtype")
    search_fields = ("text",)
    inlines = [ChoiceInline]


# --- Choice admin ---
@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct")
    list_filter = ("is_correct", "question__exam")
    search_fields = ("text",)


# --- StudentAnswer admin ---
@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ("student", "question", "choice", "text_answer", "submitted_at")
    list_filter = ("student", "question__exam")
    search_fields = ("student__email", "question__text")


# --- ExamResult admin ---
@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ("student", "exam", "score", "is_approved", "created_at")
    list_filter = ("is_approved", "exam")
    search_fields = ("student__email", "exam__title")
