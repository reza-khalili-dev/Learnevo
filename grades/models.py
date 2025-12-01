from decimal import Decimal, InvalidOperation
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Avg, Sum
from django.utils import timezone


class GradingScale(models.Model):
 
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    min_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    is_default = models.BooleanField(default=False)
    letter_grades = models.JSONField(
        default=list,
        help_text='Format: [{"letter": "A", "min": 18, "max": 20}, ...]'
    )
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.min_score}-{self.max_score})"
    
    def save(self, *args, **kwargs):
        if self.is_default:

            GradingScale.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class Grade(models.Model):

    GRADE_TYPE_CHOICES = [
        ("assignment", "Assignment/Homework"),
        ("quiz", "Quiz"),
        ("midterm", "Midterm Exam"),
        ("final", "Final Exam"),
        ("sessional", "Sessional/Classwork"),
        ("participation", "Participation"),
        ("project", "Project"),
    ]
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grades",
        limit_choices_to={"role": "student"},
        verbose_name="Student"
    )
    
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name="Course",
        null=True,  
        blank=True,
    )
    

    assignment = models.ForeignKey(
        "courses.Assignment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="grade_entries",
        verbose_name="Related Assignment"
    )
    
    exam = models.ForeignKey(
        "exams.Exam",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="grade_entries",
        verbose_name="Related Exam"
    )
    

    score = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        verbose_name="Score"
    )
    
    max_score = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        default=100,
        verbose_name="Maximum Score"
    )
    
    grade_type = models.CharField(
        max_length=20, 
        choices=GRADE_TYPE_CHOICES,
        verbose_name="Grade Type"
    )
    
    weight = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.0,
        help_text="Weight in GPA calculation (e.g., 1.0 for normal, 2.0 for important)"
    )
    
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_grades",
        limit_choices_to={"role__in": ["instructor", "employee", "manager"]},
        verbose_name="Graded By"
    )
    
    graded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Graded At"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    feedback = models.TextField(
        blank=True,
        null=True,
        verbose_name="Feedback"
    )
    
    is_published = models.BooleanField(
        default=False,
        verbose_name="Published to Student"
    )
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
        unique_together = [
            ("student", "assignment"),  
            ("student", "exam"),        
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(score__lte=models.F('max_score')),
                name="score_lte_max_score"
            ),
        ]
    
    def __str__(self):
        source = ""
        if self.assignment:
            source = f"Assignment: {self.assignment.title}"
        elif self.exam:
            source = f"Exam: {self.exam.title}"
        
        return f"{self.student.email} - {self.grade_type} - {self.score}/{self.max_score} - {source}"
    
    def clean(self):
        super().clean()
        
        if not self.assignment and not self.exam:
            raise ValidationError("Either 'assignment' or 'exam' must be set for a Grade.")
        
        if self.assignment and self.exam:
            raise ValidationError("Grade must be linked to either an assignment OR an exam, not both.")
        
        try:
            if Decimal(str(self.score)) > Decimal(str(self.max_score)):
                raise ValidationError(f"Score ({self.score}) cannot be greater than max_score ({self.max_score}).")
            if Decimal(str(self.score)) < 0:
                raise ValidationError("Score cannot be negative.")
        except (TypeError, InvalidOperation) as e:
            raise ValidationError(f"Invalid score value: {e}")
        
        if self.assignment and self.course != self.assignment.course:
            raise ValidationError("Course must match the assignment's course.")
        
        if self.exam and self.course != self.exam.course:
            raise ValidationError("Course must match the exam's course.")
    
    def save(self, *args, **kwargs):
        if self.graded_by and not self.graded_at:
            self.graded_at = timezone.now()
        
        if self.assignment and not self.course:
            self.course = self.assignment.course
        elif self.exam and not self.course:
            self.course = self.exam.course
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    
    def percentage(self):
        if self.max_score and Decimal(str(self.max_score)) != 0:
            return (Decimal(str(self.score)) / Decimal(str(self.max_score))) * Decimal(100)
        return Decimal(0)
    
    def letter_grade(self, grading_scale=None):
        if not grading_scale:
            grading_scale = GradingScale.objects.filter(is_default=True).first()
        
        if grading_scale and grading_scale.letter_grades:
            percentage = self.percentage()
            for grade_range in grading_scale.letter_grades:
                if grade_range['min'] <= percentage <= grade_range['max']:
                    return grade_range['letter']
        return None
    
    def weighted_score(self):
        return (self.percentage() * self.weight) / 100
    
    
    @classmethod
    def get_student_grades(cls, student, course=None):
        queryset = cls.objects.filter(student=student, is_published=True)
        if course:
            queryset = queryset.filter(course=course)
        return queryset
    
    @classmethod
    def calculate_gpa(cls, student, course=None):
        grades = cls.get_student_grades(student, course)
        
        if not grades.exists():
            return 0
        
        total_weighted = sum(g.weighted_score() for g in grades)
        total_weight = sum(Decimal(str(g.weight)) for g in grades)
        
        if total_weight == 0:
            return 0
        
        return total_weighted / total_weight


class ReportCard(models.Model):

    TERM_CHOICES = [
        ("fall", "Fall"),
        ("spring", "Spring"),
        ("summer", "Summer"),
        ("winter", "Winter"),
    ]
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="report_cards",
        limit_choices_to={"role": "student"}
    )
    
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="report_cards"
    )
    
    classroom = models.ForeignKey(
        "courses.Classroom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_cards"
    )
    
    term = models.CharField(max_length=20, choices=TERM_CHOICES)
    year = models.PositiveIntegerField()
    
    total_grades = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    
    is_finalized = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    
    pdf_file = models.FileField(upload_to='report_cards/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["-year", "-term"]
        verbose_name = "Report Card"
        verbose_name_plural = "Report Cards"
        unique_together = ["student", "course", "term", "year"]
    
    def __str__(self):
        return f"{self.student.email} - {self.course.title} - {self.term} {self.year}"
    
    def calculate_statistics(self):
        grades = Grade.objects.filter(
            student=self.student,
            course=self.course,
            is_published=True
        )
        
        self.total_grades = grades.count()
        
        if grades.exists():
            self.average_score = grades.aggregate(
                avg=Avg('score')
            )['avg'] or 0
            
            self.gpa = Grade.calculate_gpa(self.student, self.course)
        
        self.save()
    
    def publish(self):
        self.is_published = True
        self.published_at = timezone.now()
        self.save()