from django.db import models
from django.conf import settings

# Create your models here.


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True,null=True)

    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={"role": "Instructor"},related_name='courses')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
        