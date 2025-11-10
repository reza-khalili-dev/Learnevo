from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy

from .models import Exam, Question, Choice, StudentAnswer, ExamResult
from .forms import ExamForm, QuestionForm, ChoiceForm


class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = "exams/exam_list.html"
    context_object_name = "exams"

    def get_queryset(self):
        user = self.request.user
        if user.role == "instructor":
            return Exam.objects.filter(instructor=user)
        return Exam.objects.all()


class ExamCreateView(LoginRequiredMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = "exams/exam_form.html"

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("exams:exam_list")


class ExamUpdateView(LoginRequiredMixin, UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = "exams/exam_form.html"

    def get_success_url(self):
        return reverse("exams:exam_detail", args=[self.object.id])


class ExamDetailView(LoginRequiredMixin, DetailView):
    model = Exam
    template_name = "exams/exam_detail.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role == "student":
            return redirect("exams:exam_list")
        return super().dispatch(request, *args, **kwargs)
    
class ExamDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Exam
    template_name = "exams/exam_confirm_delete.html"
    success_url = reverse_lazy("exams:exam_list")

    def test_func(self):
        return self.request.user.role in ["manager", "employee", "instructor"]


class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "exams/question_form.html"

    def form_valid(self, form):
        exam = get_object_or_404(Exam, id=self.kwargs["exam_id"])
        form.instance.exam = exam
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exam"] = get_object_or_404(Exam, id=self.kwargs["exam_id"])
        return context

    def get_success_url(self):
        return reverse("exams:exam_detail", args=[self.kwargs["exam_id"]])


class QuestionUpdateView(LoginRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "exams/question_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["exam"] = self.object.exam
        return context

    def get_success_url(self):
        return reverse("exams:exam_detail", args=[self.object.exam.id])



class QuestionDetailView(LoginRequiredMixin, DetailView):
    model = Question
    template_name = "exams/question_detail.html"
    context_object_name = "question"
    

class QuestionDeleteView(LoginRequiredMixin, DeleteView):
    model = Question
    template_name = "exams/confirm_delete.html"

    def get_success_url(self):
        return reverse("exams:exam_detail", args=[self.object.exam.id])


class ChoiceCreateView(LoginRequiredMixin, CreateView):
    model = Choice
    form_class = ChoiceForm
    template_name = "exams/choice_form.html"

    def form_valid(self, form):
        question = get_object_or_404(Question, id=self.kwargs["question_id"])
        form.instance.question = question
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["question"] = get_object_or_404(Question, id=self.kwargs["question_id"])
        return ctx

    def get_success_url(self):
        return reverse("exams:question_detail", args=[self.kwargs["question_id"]])


class ChoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Choice
    form_class = ChoiceForm
    template_name = "exams/choice_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["question"] = self.object.question
        return ctx

    def get_success_url(self):
        return reverse("exams:question_detail", args=[self.object.question.id])

class ChoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Choice
    template_name = "exams/confirm_delete.html"

    def get_success_url(self):
        return reverse("exams:question_detail", args=[self.object.question.id])


# =============================
# Student exam views
# =============================

@login_required
def start_exam(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    
    exam_result, created = ExamResult.objects.get_or_create(
        student=request.user,
        exam=exam,
        defaults={'start_time': timezone.now()}
    )

    if not created and exam_result.start_time is None:
        exam_result.start_time = timezone.now()
        exam_result.save()

    now = timezone.now()
    if now < exam.start_time or now > exam.end_time:
        return render(request, "exams/out_of_time.html", {"exam": exam})

    first_q = exam.questions.order_by("id").first()
    if not first_q:
        return render(request, "exams/no_questions.html", {"exam": exam})

    return redirect("exams:take_question", exam_id=exam.id, question_id=first_q.id)


@login_required
def take_question(request, exam_id, question_id):
    exam = get_object_or_404(Exam, id=exam_id)
    question = get_object_or_404(Question, id=question_id, exam=exam)
    exam_result = get_object_or_404(ExamResult, exam=exam, student=request.user)

    remaining_time = (exam_result.start_time + timezone.timedelta(minutes=exam.duration) - timezone.now()).total_seconds()
    remaining_time = max(0, int(remaining_time))

    questions = list(Question.objects.filter(exam=exam).order_by("id"))
    current_index = questions.index(question)
    next_question = questions[current_index + 1] if current_index + 1 < len(questions) else None

    if request.method == "POST":
        if question.qtype in ["mcq", "audio_mcq", "image_mcq"]:
            selected_choice = request.POST.get("choice")
            StudentAnswer.objects.update_or_create(
                student=request.user,
                question=question,
                defaults={"choice_id": selected_choice, "text_answer": None}
            )
        else:
            text_answer = request.POST.get("text_answer")
            StudentAnswer.objects.update_or_create(
                student=request.user,
                question=question,
                defaults={"text_answer": text_answer, "choice_id": None}
            )

        if next_question:
            return redirect("exams:take_question", exam_id=exam.id, question_id=next_question.id)
        return redirect("exams:finish_exam", pk=exam.id)

    return render(request, "exams/take_question.html", {
        "exam": exam,
        "question": question,
        "choices": question.choices.all(),
        "remaining_time": remaining_time,
        "next_question": next_question,
    })



@login_required
def submit_answer(request, exam_id, question_id):
    question = get_object_or_404(Question, id=question_id, exam_id=exam_id)


    StudentAnswer.objects.update_or_create(
        student=request.user,
        question=question,
        defaults={
            "choice_id": request.POST.get("choice"),
            "text_answer": request.POST.get("text_answer")
        }
    )


    next_q = Question.objects.filter(exam_id=exam_id, id__gt=question.id).order_by("id").first()
    if next_q:
        return redirect("exams:take_question", exam_id=exam_id, question_id=next_q.id)
    else:
        return redirect("exams:finish_exam", pk=exam_id)

@login_required
def finish_exam(request, pk):
    exam = get_object_or_404(Exam, pk=pk)


    correct_count = StudentAnswer.objects.filter(
        student=request.user,
        question__exam=exam,
        choice__is_correct=True
    ).count()


    result, created = ExamResult.objects.update_or_create(
        student=request.user,
        exam=exam,
        defaults={"score": correct_count}
    )

    return render(request, "exams/finished.html", {"exam": exam, "score": correct_count})

