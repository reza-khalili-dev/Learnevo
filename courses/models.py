from django.db import models
from django.conf import settings
from django.forms import ValidationError

# Create your models here.


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True,null=True)

    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={"role": "Instructor"},related_name='courses')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Classroom(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='classes')
    
    title = models.CharField(max_length=200)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='enrolled_classes', blank=True, limit_choices_to={'role': 'Student'})
    capacity = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course.title} — {self.title}"

class Session(models.Model):
    classroom = models.ForeignKey('Classroom', on_delete=models.CASCADE, related_name='sessions')

    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.classroom.title} — {self.title}"
    
    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("The end time must be after the start time.")
    
    class Meta:
        ordering = ["date", "start_time"]