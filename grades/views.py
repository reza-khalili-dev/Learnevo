from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
    TemplateView
)
from django.views import View
from django.contrib import messages
from django.db.models import Q, Avg, Sum, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings 
from django.core.exceptions import PermissionDenied  

from .models import Grade, ReportCard, GradingScale
from courses.models import Course, Classroom, Submission, Assignment
from exams.models import Exam, ExamResult
from .forms import GradeForm, ReportCardForm, GradingScaleForm


# ========== Grade Views ==========

class GradeListView(LoginRequiredMixin, ListView):
    """لیست نمرات (بر اساس سطح دسترسی)"""
    model = Grade
    template_name = 'grades/grade_list.html'
    context_object_name = 'grades'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role in ['manager', 'employee']:
            # مدیران و کارمندان همه نمرات را می‌بینند
            qs = Grade.objects.all()
        elif user.role == 'instructor':
            # اساتید فقط نمرات دوره‌های خود را می‌بینند
            instructor_courses = Course.objects.filter(
                classes__instructor=user
            )
            qs = Grade.objects.filter(course__in=instructor_courses)
        elif user.role == 'student':
            # دانش‌آموزان فقط نمرات خود را می‌بینند
            qs = Grade.objects.filter(student=user, is_published=True)
        else:
            qs = Grade.objects.none()
        
        # فیلترهای اختیاری
        course_id = self.request.GET.get('course')
        if course_id:
            qs = qs.filter(course_id=course_id)
        
        grade_type = self.request.GET.get('grade_type')
        if grade_type:
            qs = qs.filter(grade_type=grade_type)
        
        student_id = self.request.GET.get('student')
        if student_id:
            qs = qs.filter(student_id=student_id)
            
        is_published = self.request.GET.get('is_published')
        if is_published == 'published':
            qs = qs.filter(is_published=True)
        elif is_published == 'unpublished':
            qs = qs.filter(is_published=False)
        
        return qs.select_related(
            'student', 'course', 'assignment', 'exam'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # ایجاد فرم فیلتر
        from .forms import GradeFilterForm
        filter_form = GradeFilterForm(self.request.GET, user=user)
        context['filter_form'] = filter_form
        
        # اضافه کردن فیلترها به context
        if user.role in ['manager', 'employee', 'instructor']:
            context['courses'] = Course.objects.all()
        elif user.role == 'student':
            context['courses'] = user.enrolled_classes.values_list('course', flat=True)
        
        return context


class GradeDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Grade
    template_name = 'grades/grade_detail.html'
    context_object_name = 'grade'
    
    def test_func(self):
        grade = self.get_object()
        user = self.request.user
        
        if user.role in ['manager', 'employee']:
            return True
        elif user.role == 'instructor':
            return grade.course.classes.filter(instructor=user).exists()
        elif user.role == 'student':
            return grade.student == user and grade.is_published
        return False


class GradeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Grade
    form_class = GradeForm
    template_name = 'grades/grade_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def test_func(self):
        user = self.request.user
        return user.role in ['manager', 'employee', 'instructor']
    
    def form_valid(self, form):
        form.instance.graded_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Grade for {form.instance.student.email} created successfully!")
        return response
    
    def get_success_url(self):
        return reverse('grades:grade_detail', kwargs={'pk': self.object.pk})


class AssignmentGradeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Grade
    form_class = GradeForm
    template_name = 'grades/grade_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(Submission, pk=kwargs['submission_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['initial'] = {
            'student': self.submission.student,
            'course': self.submission.assignment.course,
            'assignment': self.submission.assignment,
            'max_score': self.submission.assignment.max_score or 100,
            'grade_type': 'assignment',
        }
        return kwargs
    
    def test_func(self):
        user = self.request.user
        if user.role in ['manager', 'employee']:
            return True
        elif user.role == 'instructor':
            return self.submission.assignment.course.classes.filter(
                instructor=user
            ).exists()
        return False
    
    def form_valid(self, form):
        form.instance.graded_by = self.request.user
        
        existing_grade = Grade.objects.filter(
            student=self.submission.student,
            assignment=self.submission.assignment
        ).first()
        
        if existing_grade:
            existing_grade.score = form.cleaned_data['score']
            existing_grade.max_score = form.cleaned_data['max_score']
            existing_grade.feedback = form.cleaned_data.get('feedback', '')
            existing_grade.is_published = form.cleaned_data.get('is_published', False)
            existing_grade.graded_by = self.request.user
            existing_grade.save()
            self.object = existing_grade
        else:
            response = super().form_valid(form)
        
        messages.success(self.request, f"Grade for {self.submission.student.email} saved successfully!")
        return response if 'response' in locals() else redirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse('courses:assignment_detail', kwargs={'pk': self.submission.assignment.pk})


class GradeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Grade
    form_class = GradeForm
    template_name = 'grades/grade_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def test_func(self):
        grade = self.get_object()
        user = self.request.user
        
        if user.role in ['manager', 'employee']:
            return True
        elif user.role == 'instructor':
            return grade.course.classes.filter(instructor=user).exists()
        return False
    
    def form_valid(self, form):
        form.instance.graded_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Grade updated successfully!")
        return response
    
    def get_success_url(self):
        return reverse('grades:grade_detail', kwargs={'pk': self.object.pk})


class GradeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Grade
    template_name = 'grades/grade_confirm_delete.html'
    
    def test_func(self):
        grade = self.get_object()
        user = self.request.user
        return user.role in ['manager', 'employee']
    
    def get_success_url(self):
        return reverse('grades:grade_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Grade deleted successfully!")
        return super().delete(request, *args, **kwargs)


class BulkGradePublishView(LoginRequiredMixin, UserPassesTestMixin, View):
    
    def test_func(self):
        return self.request.user.role in ['manager', 'employee', 'instructor']
    
    def post(self, request, *args, **kwargs):
        grade_ids = request.POST.getlist('grade_ids')
        action = request.POST.get('action')
        
        if not grade_ids:
            messages.error(request, "No grades selected.")
            return redirect('grades:grade_list')
        
        grades = Grade.objects.filter(id__in=grade_ids)
        
        user = request.user
        if user.role == 'instructor':
            instructor_courses = Course.objects.filter(classes__instructor=user)
            grades = grades.filter(course__in=instructor_courses)
        
        if action == 'publish':
            grades.update(is_published=True)
            messages.success(request, f"{grades.count()} grades published successfully!")
        elif action == 'unpublish':
            grades.update(is_published=False)
            messages.success(request, f"{grades.count()} grades unpublished successfully!")
        
        return redirect('grades:grade_list')


# ========== Report Card Views ==========

class ReportCardListView(LoginRequiredMixin, ListView):
    model = ReportCard
    template_name = 'grades/reportcard_list.html'
    context_object_name = 'report_cards'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role in ['manager', 'employee']:
            qs = ReportCard.objects.all()
        elif user.role == 'instructor':
            instructor_courses = Course.objects.filter(classes__instructor=user)
            qs = ReportCard.objects.filter(course__in=instructor_courses)
        elif user.role == 'student':
            qs = ReportCard.objects.filter(student=user, is_published=True)
        else:
            qs = ReportCard.objects.none()
        
        return qs.select_related('student', 'course', 'classroom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.role in ['manager', 'employee']:
            context['total_report_cards'] = ReportCard.objects.count()
            context['published_count'] = ReportCard.objects.filter(is_published=True).count()
            context['average_gpa'] = ReportCard.objects.filter(
                is_finalized=True
            ).aggregate(avg=Avg('gpa'))['avg'] or 0
        
        return context


class ReportCardDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = ReportCard
    template_name = 'grades/reportcard_detail.html'
    context_object_name = 'report_card'
    
    def test_func(self):
        report_card = self.get_object()
        user = self.request.user
        
        if user.role in ['manager', 'employee']:
            return True
        elif user.role == 'instructor':
            return report_card.course.classes.filter(instructor=user).exists()
        elif user.role == 'student':
            return report_card.student == user and report_card.is_published
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        grades = Grade.objects.filter(
            student=self.object.student,
            course=self.object.course,
            is_published=True
        ).select_related('assignment', 'exam')
        
        context['grades'] = grades
        context['grade_types'] = Grade.GRADE_TYPE_CHOICES
        
        return context


class ReportCardCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ReportCard
    form_class = ReportCardForm
    template_name = 'grades/reportcard_form.html'
    
    def test_func(self):
        return self.request.user.role in ['manager', 'employee']
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        self.object.calculate_statistics()
        
        messages.success(self.request, "Report card created successfully!")
        return response
    
    def get_success_url(self):
        return reverse('grades:reportcard_detail', kwargs={'pk': self.object.pk})


class ReportCardPublishView(LoginRequiredMixin, UserPassesTestMixin, View):
    
    def test_func(self):
        return self.request.user.role in ['manager', 'employee', 'instructor']
    
    def post(self, request, pk):
        report_card = get_object_or_404(ReportCard, pk=pk)
        
        user = request.user
        if user.role == 'instructor':
            if not report_card.course.classes.filter(instructor=user).exists():
                raise PermissionDenied("You don't have permission to publish this report card.")
        
        report_card.publish()
        messages.success(request, "Report card published successfully!")
        
        return redirect('grades:reportcard_detail', pk=report_card.pk)


class ReportCardPDFView(LoginRequiredMixin, UserPassesTestMixin, View):
    
    def test_func(self):
        report_card = get_object_or_404(ReportCard, pk=self.kwargs['pk'])
        user = self.request.user
        
        if user.role in ['manager', 'employee']:
            return True
        elif user.role == 'instructor':
            return report_card.course.classes.filter(instructor=user).exists()
        elif user.role == 'student':
            return report_card.student == user and report_card.is_published
        return False
    
    def get(self, request, pk):
        from django.http import FileResponse
        import os
        
        report_card = get_object_or_404(ReportCard, pk=pk)
        
        if report_card.pdf_file:
            response = FileResponse(
                report_card.pdf_file.open(),
                as_attachment=True,
                filename=f"report_card_{report_card.student.email}_{report_card.term}_{report_card.year}.pdf"
            )
            return response
        
        messages.error(request, "PDF file not available.")
        return redirect('grades:reportcard_detail', pk=pk)


# ========== Dashboard & Analytics ==========

class GradesDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'grades/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.role in ['manager', 'employee']:
            context['total_grades'] = Grade.objects.count()
            context['published_grades'] = Grade.objects.filter(is_published=True).count()
            context['total_students'] = user.__class__.objects.filter(role='student').count()
            context['total_courses'] = Course.objects.count()
            
            grade_distribution = Grade.objects.filter(is_published=True).values(
                'grade_type'
            ).annotate(
                count=Count('id'),
                avg_score=Avg('score')
            ).order_by('grade_type')
            
            context['grade_distribution'] = list(grade_distribution)
            
        elif user.role == 'instructor':
            instructor_courses = Course.objects.filter(classes__instructor=user)
            context['my_courses'] = instructor_courses
            
            grades = Grade.objects.filter(course__in=instructor_courses)
            context['total_grades'] = grades.count()
            context['unpublished_grades'] = grades.filter(is_published=False).count()
            
        elif user.role == 'student':
            context['my_grades'] = Grade.objects.filter(
                student=user, 
                is_published=True
            ).count()
            
            context['my_report_cards'] = ReportCard.objects.filter(
                student=user,
                is_published=True
            ).count()
            
            context['overall_gpa'] = Grade.calculate_gpa(user)
            
            context['recent_grades'] = Grade.objects.filter(
                student=user,
                is_published=True
            ).select_related('course', 'assignment', 'exam')[:10]
        
        return context


class StudentGradesView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = settings.AUTH_USER_MODEL
    template_name = 'grades/student_grades.html'
    context_object_name = 'student'
    slug_field = 'id'
    slug_url_kwarg = 'student_id'
    
    def test_func(self):
        user = self.request.user
        student = self.get_object()
        
        if user.role in ['manager', 'employee']:
            return True
        elif user.role == 'instructor':
            instructor_courses = Course.objects.filter(classes__instructor=user)
            student_courses = student.enrolled_classes.values_list('course', flat=True)
            return bool(set(instructor_courses) & set(student_courses))
        elif user.role == 'student':
            return user == student
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object
        
        grades = Grade.objects.filter(
            student=student,
            is_published=True
        ).select_related('course', 'assignment', 'exam')
        
        context['grades'] = grades
        
        grades_by_course = {}
        for grade in grades:
            course_name = grade.course.title
            if course_name not in grades_by_course:
                grades_by_course[course_name] = []
            grades_by_course[course_name].append(grade)
        
        context['grades_by_course'] = grades_by_course
        
        context['report_cards'] = ReportCard.objects.filter(
            student=student,
            is_published=True
        ).select_related('course')
        
        return context


# ========== API Views ==========

class GradeStatisticsAPIView(LoginRequiredMixin, View):
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        if user.role not in ['manager', 'employee', 'instructor']:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        course_id = request.GET.get('course_id')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        filters = Q()
        
        if course_id:
            filters &= Q(course_id=course_id)
        
        if start_date and end_date:
            filters &= Q(created_at__date__range=[start_date, end_date])
        
        if user.role == 'instructor':
            instructor_courses = Course.objects.filter(classes__instructor=user)
            filters &= Q(course__in=instructor_courses)
        
        grades = Grade.objects.filter(filters, is_published=True)
        
        statistics = {
            'total_grades': grades.count(),
            'average_score': grades.aggregate(avg=Avg('score'))['avg'] or 0,
            'grade_distribution': list(
                grades.values('grade_type').annotate(
                    count=Count('id'),
                    average=Avg('score')
                ).order_by('grade_type')
            ),
            'top_students': list(
                grades.values('student__email', 'student__first_name', 'student__last_name')
                .annotate(average=Avg('score'), count=Count('id'))
                .order_by('-average')[:10]
            )
        }
        
        return JsonResponse(statistics)


# ========== Grading Scale Views ==========

class GradingScaleListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = GradingScale
    template_name = 'grades/gradingscale_list.html'
    context_object_name = 'scales'
    
    def test_func(self):
        return self.request.user.role in ['manager', 'employee']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['default_scale'] = GradingScale.objects.filter(is_default=True).first()
        return context


class GradingScaleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = GradingScale
    form_class = GradingScaleForm
    template_name = 'grades/gradingscale_form.html'
    success_url = reverse_lazy('grades:gradingscale_list')
    
    def test_func(self):
        return self.request.user.role in ['manager', 'employee']
    
    def form_valid(self, form):
        messages.success(self.request, "Grading scale created successfully!")
        return super().form_valid(form)


class GradingScaleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = GradingScale
    form_class = GradingScaleForm
    template_name = 'grades/gradingscale_form.html'
    success_url = reverse_lazy('grades:gradingscale_list')
    
    def test_func(self):
        return self.request.user.role in ['manager', 'employee']
    
    def form_valid(self, form):
        messages.success(self.request, "Grading scale updated successfully!")
        return super().form_valid(form)


class GradingScaleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = GradingScale
    template_name = 'grades/gradingscale_confirm_delete.html'
    success_url = reverse_lazy('grades:gradingscale_list')
    
    def test_func(self):
        return self.request.user.role in ['manager', 'employee']
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Grading scale deleted successfully!")
        return super().delete(request, *args, **kwargs)