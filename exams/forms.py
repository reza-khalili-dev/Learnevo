from django import forms
from .models import Exam, Question, Choice

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ["course", "title", "description", "duration", "start_time", "end_time"]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "qtype", "points", "audio_file", "image_file", "order"]

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ["text", "is_correct"]
        widgets = {
            "text": forms.TextInput(attrs={"class": "form-control", "placeholder": "Choice text"}),
            "is_correct": forms.CheckboxInput(),
        }