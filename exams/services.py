from .models import ExamResult, StudentAnswer, Choice


def calculate_exam_score(student, exam):
    answers = StudentAnswer.objects.filter(student=student, question__exam=exam)
    total_score = 0
    for answer in answers:
        if answer.choice.is_correct:
            total_score += answer.question.points
    result, created = ExamResult.objects.update_or_create(
        student=student,
        exam=exam,
        defaults={"score": total_score, "is_approved": True},
    )
    return result
