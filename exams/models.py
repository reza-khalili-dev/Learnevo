from django.db import models
from django.conf import settings
from courses.models import Course 
from django.utils import timezone


class Exam(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams', null=True, blank=True)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_exams',
        limit_choices_to={"role": "instructor"},
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.PositiveIntegerField(help_text='Exam duration (minutes)')
    total_marks = models.PositiveIntegerField(default=0, help_text="Total marks for the exam (auto-calculated or set manually)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = [
        ("mcq", "Multiple Choice"),
        ("essay", "Essay / Open Response"),
        ("audio_mcq", "Listening (Audio) + MCQ"),
        ("audio_essay", "Listening (Audio) + Essay"),
        ("image_mcq", "Image + MCQ"),
        ("image_essay", "Image + Essay"),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    qtype = models.CharField(max_length=20, choices=QUESTION_TYPES, default="mcq")
    points = models.PositiveIntegerField(default=1)
    # optional media fields for audio/image prompts
    audio_file = models.FileField(upload_to='exam_media/audio/', null=True, blank=True)
    image_file = models.ImageField(upload_to='exam_media/images/', null=True, blank=True)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.text[:60]}..."


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.TextField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({'Correct' if self.is_correct else 'Incorrect'})"


class StudentAnswer(models.Model):
    """
    Support both MCQ answers (choice) and written answers (text).
    For MCQ, `choice` is set. For essay/open response, `text_answer` is set.
    We keep both fields nullable; one of them must be provided (validate in forms/views).
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answers',
        limit_choices_to={"role": "student"}
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    # For MCQ answers:
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    # For essay/open answers:
    text_answer = models.TextField(null=True, blank=True)
    # optionally store upload (e.g., audio response) — not used now, but reserved:
    uploaded_file = models.FileField(upload_to='exam_responses/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "question")

    def __str__(self):
        return f"{self.student.email} → {self.question.text[:30]}..."




class ExamResult(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exam_results",
        limit_choices_to={"role": "student"},
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="results")
    score = models.FloatField(default=0)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True, blank=True)  # اضافه شد

    class Meta:
        unique_together = ("student", "exam")

    def __str__(self):
        return f"{self.student.email} - {self.exam.title} - {self.score}"
