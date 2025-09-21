from django import forms
from .models import Session, Attendance


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ["title", "description", "start_time", "end_time"]

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