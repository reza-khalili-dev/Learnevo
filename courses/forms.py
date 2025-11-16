from django import forms

from users.signals import User
from .models import Classroom, Session, Attendance, Assignment, Submission
from django.utils import timezone





class ClassForm(forms.ModelForm):
    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role='student'),
        required=False,
        widget=forms.CheckboxSelectMultiple, 
        label="Students"
    )

    class Meta:
        model = Classroom
        fields = ['course', 'instructor', 'title', 'description', 'start_date', 'end_date', 'capacity', 'students']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['instructor'].queryset = User.objects.filter(role='instructor')
        
        
class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ["title", "description", "start_time", "end_time"]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")
        if start and end and end <= start:
            raise forms.ValidationError("The end time must be after the start time.")
        return cleaned_data


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["status", "note"]

    def clean(self):
        cleaned =  super().clean()
        return cleaned
    

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["title", "description", "attachment", "due_date", "max_score", "is_published", "session"]

    def clean_due_date(self):
        due = self.cleaned_data.get("due_date")
        if due and due <= timezone.now():
            raise forms.ValidationError("Due date must be in the future.")
        return due

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["content", "file"]

    def clean(self):
        cleaned = super().clean()
        content = cleaned.get("content")
        file = cleaned.get("file")
        if not content and not file:
            raise forms.ValidationError("You must provide either text content or a file.")
        return cleaned
