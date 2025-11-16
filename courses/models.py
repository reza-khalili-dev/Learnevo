from django.db import models
from django.conf import settings
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
import os
from django.utils import timezone
# Create your models here.

# Dinamic upload func
def submission_upload_to(instance, filename):
    return os.path.join("assignments",str(instance.assignment.id),str(instance.student.id),filename)


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Classroom(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='classes')
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   limit_choices_to={'role': 'instructor'},
                                   related_name='instructed_classes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True,null=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                      related_name='enrolled_classes',
                                      blank=True,
                                      limit_choices_to={'role': 'student'})
    capacity = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course.title} — {self.title}"




class Session(models.Model):
    classroom = models.ForeignKey(
        "Classroom",
        on_delete=models.CASCADE,
        related_name="sessions"
    )

    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()

        if not self.classroom_id:
            return 

        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError(_("End time must be after start time."))

            if self.classroom.start_date and self.classroom.end_date:
                if not (self.classroom.start_date <= self.start_time.date() <= self.classroom.end_date):
                    raise ValidationError(_("Session start time must be within the classroom date range."))
                if not (self.classroom.start_date <= self.end_time.date() <= self.classroom.end_date):
                    raise ValidationError(_("Session end time must be within the classroom date range."))

            overlapping_sessions = (
                Session.objects
                .filter(classroom=self.classroom)
                .exclude(pk=self.pk)
                .filter(
                    start_time__lt=self.end_time,
                    end_time__gt=self.start_time
                )
            )

            if overlapping_sessions.exists():
                overlaps = ", ".join([s.title for s in overlapping_sessions])
                raise ValidationError(_(f"Session overlaps with other sessions: {overlaps}"))


    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        if not self.classroom_id:
            return f"Session — {self.title}"
        return f"{self.classroom.title} — {self.title}"


class Attendance(models.Model):
    
    STATUS_PRESENT = "present"
    STATUS_ABSENT  = "absent"
    STATUS_LATE    = "late"
    STATUS_EXCUSED = "excused"
    
    STATUS_CHOICES = [
        (STATUS_PRESENT, "Present"),
        (STATUS_ABSENT,  "Absent"),
        (STATUS_LATE,    "Late"),
        (STATUS_EXCUSED, "Excused"),
    ]

    session = models.ForeignKey("Session",on_delete=models.CASCADE,related_name="attendances")
    student = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="attendances")
    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default=STATUS_ABSENT)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="marked_attendances")

    marked_at = models.DateTimeField(auto_now=True)
    note  = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('session','student')
        ordering = ["student__last_name", "student__first_name"]
    
    def __str__(self):
        return f"{self.student} — {self.session} — {self.status}"
    
    def clean(self):
        if getattr(self.student, 'role', None) != 'student':
            raise ValidationError(_('Selected user is not a student.'))
        
        classroom = self.session.classroom
        if not classroom.students.filter(pk=self.student.pk).exists():
            raise ValidationError(_('Student is not enrolled in this classroom.'))

# Assignment Model
class Assignment(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='assignments')
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments")
        
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to="assignments/attachments/", null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    max_score = models.PositiveIntegerField(default=100)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.title} — {self.title}"
    
    def clean(self):
        if self.due_date and self.created_at and self.due_date <= self.created_at:
            raise ValidationError(_("Due date must be after creation date."))
        
        
# Submission Model
class Submission(models.Model):
    
    assignment = models.ForeignKey(Assignment,on_delete=models.CASCADE,related_name="submissions")
    student = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="submissions")
    
    content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=submission_upload_to, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="graded_submissions")
    graded_at = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("assignment", "student")
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Submission {self.assignment.title} by {self.student}"
    
    def clean(self):
        course = self.assignment.course
        classrooms = course.classes.all()
        enrolled = False
        for cl in classrooms:
            if cl.students.filter(pk=self.student.pk).exists():
                enrolled = True
                break
        if not enrolled:
            raise ValidationError(_("Student is not enrolled in any classroom of this course."))

        if self.assignment.due_date and self.submitted_at:
            if timezone.now() > self.assignment.due_date:
                raise ValidationError(_("The deadline for this assignment has passed."))

    