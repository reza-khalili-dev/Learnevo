from .models import ExamResult, StudentAnswer, Choice


def calculate_exam_score(student, exam):
    answers = StudentAnswer.objects.filter(student=student, question__exam=exam)
    total_score = 0
    total_possible = 0
    for question in exam.questions.all():
        total_possible += question.points
    for ans in answers.select_related('question', 'choice'):
        if ans.choice and getattr(ans.choice, "is_correct", False):
            total_score += ans.question.points
    result, created = ExamResult.objects.update_or_create(
        student=student,
        exam=exam,
        defaults={"score": total_score, "is_approved": True},
    )
    return result
