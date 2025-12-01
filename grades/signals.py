
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone

from .models import Grade, ReportCard
from courses.models import Submission
from exams.models import ExamResult


@receiver(post_save, sender=Submission)
def create_grade_for_new_submission(sender, instance, created, **kwargs):

    if created:
        if instance.assignment:
            
            if not Grade.objects.filter(
                student=instance.student,
                assignment=instance.assignment
            ).exists():
                
                Grade.objects.create(
                    student=instance.student,
                    course=instance.assignment.course,
                    assignment=instance.assignment,
                    score=0,  
                    max_score=instance.assignment.max_score or 100,
                    grade_type="assignment",
                    is_published=False
                )


@receiver(post_save, sender=ExamResult)
def create_or_update_grade_from_examresult(sender, instance, created, **kwargs):

    if instance.is_approved:  
        with transaction.atomic():
            grade, created = Grade.objects.update_or_create(
                student=instance.student,
                exam=instance.exam,
                defaults={
                    'course': instance.exam.course,
                    'score': instance.score,
                    'max_score': instance.exam.total_marks or 100,
                    'grade_type': 'final' if 'final' in instance.exam.title.lower() else 'midterm',
                    'graded_at': timezone.now(),
                    'is_published': True  
                }
            )


@receiver(post_save, sender=Grade)
def update_report_card_on_grade_change(sender, instance, **kwargs):

    if instance.is_published:  
        current_year = timezone.now().year
        current_month = timezone.now().month
        
        if current_month in [9, 10, 11, 12]:
            term = "fall"
        elif current_month in [1, 2, 3, 4, 5]:
            term = "spring"
        else:
            term = "summer"
        
        report_card, created = ReportCard.objects.get_or_create(
            student=instance.student,
            course=instance.course,
            term=term,
            year=current_year,
            defaults={
                'classroom': instance.course.classes.first()
            }
        )
        
        report_card.calculate_statistics()


@receiver(post_delete, sender=Grade)
def update_report_card_on_grade_delete(sender, instance, **kwargs):

    if instance.is_published:
        report_cards = ReportCard.objects.filter(
            student=instance.student,
            course=instance.course
        )
        
        for report_card in report_cards:
            report_card.calculate_statistics()



@receiver(post_save, sender=Grade)
def notify_student_on_grade_publish(sender, instance, **kwargs):

    if instance.is_published and instance.pk:
        from django.contrib import messages
        pass



@receiver(post_save, sender='courses.Course')
def create_grading_scale_for_course(sender, instance, created, **kwargs):

    if created:
        from .models import GradingScale
        
        if not GradingScale.objects.filter(is_default=True).exists():
            GradingScale.objects.create(
                name=f"Default Scale - {instance.title}",
                min_score=0,
                max_score=20,
                letter_grades=[
                    {"letter": "A+", "min": 19, "max": 20},
                    {"letter": "A", "min": 18, "max": 18.99},
                    {"letter": "B+", "min": 17, "max": 17.99},
                    {"letter": "B", "min": 16, "max": 16.99},
                    {"letter": "C+", "min": 15, "max": 15.99},
                    {"letter": "C", "min": 14, "max": 14.99},
                    {"letter": "D", "min": 12, "max": 13.99},
                    {"letter": "F", "min": 0, "max": 11.99},
                ],
                is_default=True
            )