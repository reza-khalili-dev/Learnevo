from django import forms
from .models import Exam, Question

class QuestionInlineForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "qtype", "points", "audio_file", "image_file", "order"]
        widgets = {
            "text": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "qtype": forms.Select(attrs={"class": "form-select"}),
            "points": forms.NumberInput(attrs={"class": "form-control"}),
            "audio_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "image_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ["title", "description", "course", "instructor", "start_time", "end_time", "duration"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "course": forms.Select(attrs={"class": "form-select"}),
            "instructor": forms.Select(attrs={"class": "form-select"}),
            "start_time": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "duration": forms.NumberInput(attrs={"class": "form-control"}),
        }
