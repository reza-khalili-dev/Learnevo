from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Grade, ReportCard, GradingScale
from courses.models import Course, Classroom, Assignment, Submission
from exams.models import Exam

User = get_user_model()


class GradeForm(forms.ModelForm):
    
    class Meta:
        model = Grade
        fields = [
            'student', 'course', 'assignment', 'exam',
            'score', 'max_score', 'grade_type', 'weight',
            'feedback', 'is_published'
        ]
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'assignment': forms.Select(attrs={'class': 'form-control'}),
            'exam': forms.Select(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '1'
            }),
            'grade_type': forms.Select(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.1',
                'max': '5.0'
            }),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter feedback for the student...'
            }),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'weight': 'Weight in GPA calculation (e.g., 1.0 = normal, 2.0 = double weight)',
            'score': f'Score out of max_score',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            if self.user.role in ['manager', 'employee']:
                self.fields['student'].queryset = User.objects.filter(role='student')
                self.fields['course'].queryset = Course.objects.all()
                self.fields['assignment'].queryset = Assignment.objects.all()
                self.fields['exam'].queryset = Exam.objects.all()
            
            elif self.user.role == 'instructor':
                instructor_courses = Course.objects.filter(classes__instructor=self.user)
                
                self.fields['student'].queryset = User.objects.filter(
                    role='student',
                    enrolled_classes__course__in=instructor_courses
                ).distinct()
                
                self.fields['course'].queryset = instructor_courses
                self.fields['assignment'].queryset = Assignment.objects.filter(
                    course__in=instructor_courses
                )
                self.fields['exam'].queryset = Exam.objects.filter(
                    instructor=self.user
                )
            
            else:
                self.fields['student'].queryset = User.objects.none()
                self.fields['course'].queryset = Course.objects.none()
                self.fields['assignment'].queryset = Assignment.objects.none()
                self.fields['exam'].queryset = Exam.objects.none()
        
        self.fields['assignment'].required = False
        self.fields['exam'].required = False
        
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
        
        if 'is_published' in self.fields:
            self.fields['is_published'].widget.attrs['class'] = 'form-check-input'
    
    def clean(self):
        cleaned_data = super().clean()
        
        student = cleaned_data.get('student')
        assignment = cleaned_data.get('assignment')
        exam = cleaned_data.get('exam')
        score = cleaned_data.get('score')
        max_score = cleaned_data.get('max_score')
        
        if assignment and exam:
            raise forms.ValidationError(
                "You must select either an assignment OR an exam, not both."
            )
        
        if not assignment and not exam:
            raise forms.ValidationError(
                "You must select either an assignment or an exam."
            )
        
        if score is not None and max_score is not None:
            if score > max_score:
                raise forms.ValidationError(
                    f"Score ({score}) cannot be greater than maximum score ({max_score})."
                )
            if score < 0:
                raise forms.ValidationError("Score cannot be negative.")
        
        if assignment and student:
            if not Submission.objects.filter(
                assignment=assignment,
                student=student
            ).exists():
                raise forms.ValidationError(
                    f"Student {student.email} has not submitted this assignment."
                )
        
        return cleaned_data


class GradeBulkForm(forms.Form):
    
    grade_type = forms.ChoiceField(
        choices=Grade.GRADE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    max_score = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        initial=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '1'
        })
    )
    weight = forms.DecimalField(
        max_digits=4,
        decimal_places=2,
        initial=1.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.1',
            'max': '5.0'
        })
    )
    is_published = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class ReportCardForm(forms.ModelForm):
    
    class Meta:
        model = ReportCard
        fields = [
            'student', 'course', 'classroom', 'term', 'year',
            'is_finalized', 'is_published'
        ]
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'classroom': forms.Select(attrs={'class': 'form-control'}),
            'term': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2000',
                'max': '2100'
            }),
            'is_finalized': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            if self.user.role in ['manager', 'employee']:
                self.fields['student'].queryset = User.objects.filter(role='student')
                self.fields['course'].queryset = Course.objects.all()
                self.fields['classroom'].queryset = Classroom.objects.all()
            
            elif self.user.role == 'instructor':
                instructor_courses = Course.objects.filter(classes__instructor=self.user)
                
                self.fields['student'].queryset = User.objects.filter(
                    role='student',
                    enrolled_classes__course__in=instructor_courses
                ).distinct()
                
                self.fields['course'].queryset = instructor_courses
                self.fields['classroom'].queryset = Classroom.objects.filter(
                    course__in=instructor_courses
                )
        
        if not self.instance.pk:  
            self.fields['year'].initial = timezone.now().year
        
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        
        student = cleaned_data.get('student')
        course = cleaned_data.get('course')
        classroom = cleaned_data.get('classroom')
        year = cleaned_data.get('year')
        term = cleaned_data.get('term')
        
        if student and course:
            if not student.enrolled_classes.filter(course=course).exists():
                raise forms.ValidationError(
                    f"Student {student.email} is not enrolled in {course.title}."
                )
        
        if classroom and course:
            if classroom.course != course:
                raise forms.ValidationError(
                    f"Classroom {classroom.title} does not belong to course {course.title}."
                )
        
        if student and classroom:
            if not classroom.students.filter(id=student.id).exists():
                raise forms.ValidationError(
                    f"Student {student.email} is not in classroom {classroom.title}."
                )
        
        if student and course and year and term:
            existing = ReportCard.objects.filter(
                student=student,
                course=course,
                year=year,
                term=term
            )
            
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    f"A report card already exists for {student.email} in "
                    f"{course.title} - {term} {year}."
                )
        
        return cleaned_data


class GradingScaleForm(forms.ModelForm):
    
    class Meta:
        model = GradingScale
        fields = ['name', 'description', 'min_score', 'max_score', 
                 'letter_grades', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'min_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'letter_grades': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Format: [{"letter": "A+", "min": 19, "max": 20}, ...]'
            }),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'letter_grades': 'Enter valid JSON array of objects with "letter", "min", "max" keys',
            'min_score': 'Minimum possible score (usually 0)',
            'max_score': 'Maximum possible score (e.g., 20, 100)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
    
    def clean_letter_grades(self):
        import json
        
        letter_grades = self.cleaned_data.get('letter_grades')
        
        if not letter_grades:
            return []
        
        try:
            grades_list = json.loads(letter_grades)
            
            if not isinstance(grades_list, list):
                raise forms.ValidationError("Letter grades must be a JSON array.")
            
            required_keys = {'letter', 'min', 'max'}
            for i, grade in enumerate(grades_list):
                if not isinstance(grade, dict):
                    raise forms.ValidationError(
                        f"Item {i+1} must be a JSON object."
                    )
                
                missing_keys = required_keys - set(grade.keys())
                if missing_keys:
                    raise forms.ValidationError(
                        f"Item {i+1} missing keys: {', '.join(missing_keys)}"
                    )
                
                try:
                    min_val = float(grade['min'])
                    max_val = float(grade['max'])
                except ValueError:
                    raise forms.ValidationError(
                        f"Item {i+1}: min and max must be numbers."
                    )
                
                if min_val > max_val:
                    raise forms.ValidationError(
                        f"Item {i+1}: min ({min_val}) cannot be greater than max ({max_val})."
                    )
            
            sorted_grades = sorted(grades_list, key=lambda x: x['min'])
            for i in range(len(sorted_grades) - 1):
                current_max = sorted_grades[i]['max']
                next_min = sorted_grades[i + 1]['min']
                
                if current_max >= next_min:
                    raise forms.ValidationError(
                        f"Grade ranges overlap: {sorted_grades[i]['letter']} "
                        f"({current_max}) and {sorted_grades[i+1]['letter']} ({next_min})"
                    )
            
            return grades_list
            
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"Invalid JSON: {str(e)}")
    
    def clean(self):
        cleaned_data = super().clean()
        
        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        
        if min_score is not None and max_score is not None:
            if min_score >= max_score:
                raise forms.ValidationError(
                    f"Minimum score ({min_score}) must be less than maximum score ({max_score})."
                )
        
        letter_grades = cleaned_data.get('letter_grades', [])
        if letter_grades and min_score is not None and max_score is not None:
            first_min = min(grade['min'] for grade in letter_grades)
            last_max = max(grade['max'] for grade in letter_grades)
            
            if first_min < float(min_score):
                raise forms.ValidationError(
                    f"First grade range starts at {first_min}, "
                    f"but minimum score is {min_score}."
                )
            
            if last_max > float(max_score):
                raise forms.ValidationError(
                    f"Last grade range ends at {last_max}, "
                    f"but maximum score is {max_score}."
                )
        
        return cleaned_data


class GradeFilterForm(forms.Form):
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    grade_type = forms.ChoiceField(
        choices=[('', 'All')] + Grade.GRADE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(role='student'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    is_published = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('published', 'Published Only'),
            ('unpublished', 'Unpublished Only')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            if self.user.role in ['manager', 'employee']:
                pass
            elif self.user.role == 'instructor':
                instructor_courses = Course.objects.filter(classes__instructor=self.user)
                self.fields['course'].queryset = instructor_courses
                self.fields['student'].queryset = User.objects.filter(
                    role='student',
                    enrolled_classes__course__in=instructor_courses
                ).distinct()
            elif self.user.role == 'student':
                self.fields['student'].queryset = User.objects.filter(id=self.user.id)
                self.fields['student'].initial = self.user
                self.fields['student'].widget.attrs['readonly'] = True
                self.fields['student'].disabled = True


class ReportCardFilterForm(forms.Form):
    
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(role='student'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    term = forms.ChoiceField(
        choices=[('', 'All')] + ReportCard.TERM_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    year = forms.ChoiceField(
        choices=[('', 'All')] + [(str(y), str(y)) for y in range(2020, timezone.now().year + 5)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_published = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('published', 'Published Only'),
            ('unpublished', 'Unpublished Only')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            if self.user.role == 'instructor':
                instructor_courses = Course.objects.filter(classes__instructor=self.user)
                self.fields['course'].queryset = instructor_courses
                self.fields['student'].queryset = User.objects.filter(
                    role='student',
                    enrolled_classes__course__in=instructor_courses
                ).distinct()
            elif self.user.role == 'student':
                self.fields['student'].queryset = User.objects.filter(id=self.user.id)
                self.fields['student'].initial = self.user
                self.fields['student'].widget.attrs['readonly'] = True
                self.fields['student'].disabled = True