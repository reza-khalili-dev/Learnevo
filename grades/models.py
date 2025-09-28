from decimal import Decimal, InvalidOperation
from django.db import models
from django.conf import settings
from exams.models import Exam
from courses.models import Assignment
from django.core.exceptions import ValidationError


# Create your models here.


class Grades(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='grades', limit_choices_to={"role": "student"})
    exam = models.ForeignKey("exams.Exam",  on_delete=models.CASCADE, null=True , blank=True, related_name='grades')
    assignment = models.ForeignKey("courses.Assignment",null=True, blank=True, on_delete=models.CASCADE,related_name='grades')
    score = models.DecimalField(max_digits=6, decimal_places=2)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=20)

    GRADE_TYPE_CHOICES = [
        ("sessional", "Sessional"),
        ("final", "Final"),
        ("midterm", "Midterm"),
        ("assignment", "Assignment"),
        ("exam", "Exam"),
    ]
    grade_type = models.CharField(max_length=20, choices=GRADE_TYPE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return  f"{self.student.email} - {self.grade_type} - {self.score}/{self.max_score}"
    
    def clean(self):
        if not self.exam and not self.assignment:
            raise ValidationError("Either 'exam' or 'assignment' must be set for a Grade.")
    
        if self.exam and self.assignment:
            raise ValidationError("Grade must be linked to either an exam OR an assignment, not both.")
        try:
            if Decimal(self.score) > Decimal(self.max_score):
                raise ValidationError("Score cannot be greater than max_score.")
        except (TypeError, InvalidOperation):
            pass
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def percentage(self):
        if self.max_score and Decimal(self.max_score) != 0:
            return (Decimal(self.score) / Decimal(self.max_score)) * Decimal(100)
        return Decimal(0)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
        
