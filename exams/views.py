from django.shortcuts import get_object_or_404,render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from .models import  Exam, Question, StudentAnswer, ExamResult
from .forms import ExamForm, QuestionForm, ChoiceForm, Choice

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


class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "exams/question_form.html"

    def form_valid(self, form):
        exam_id = self.kwargs["exam_id"]
        form.instance.exam_id = exam_id
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("exams:exam_detail", args=[self.kwargs["exam_id"]])


class QuestionUpdateView(LoginRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "exams/question_form.html"

    def get_success_url(self):
        return reverse("exams:exam_detail", args=[self.object.exam.id])

class QuestionDetailView(LoginRequiredMixin, DetailView):
    model = Question
    template_name = "exams/question_detail.html"
    context_object_name = "question"


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
    

@login_required
def start_exam(request, pk):
    exam = get_object_or_404(Exam, pk=pk)

    # student already took exam?
    if ExamResult.objects.filter(student=request.user, exam=exam).exists():
        return render(request, "exams/already_taken.html", {"exam": exam})

    # time check
    now = timezone.now()
    if now < exam.start_time or now > exam.end_time:
        return render(request, "exams/out_of_time.html", {"exam": exam})

    first_q = exam.questions.order_by("order").first()
    if not first_q:
        # اگر سوالی وجود ندارد
        return render(request, "exams/no_questions.html", {"exam": exam})

    # فقط question_id را ارسال کن، order لازم نیست
    return redirect("exams:take_question", exam_id=exam.id, question_id=first_q.id)


@login_required
def take_question(request, exam_id, question_id):
    exam = get_object_or_404(Exam, id=exam_id)
    question = get_object_or_404(Question, id=question_id, exam=exam)

    # همه سوالات مربوط به این امتحان
    questions = list(Question.objects.filter(exam=exam).order_by("id"))

    # گرفتن index سؤال فعلی
    current_index = questions.index(question)

    # انتخاب سوال بعدی
    next_question = questions[current_index + 1] if current_index + 1 < len(questions) else None

    if request.method == "POST":
        selected_choice = request.POST.get("choice")
        text_answer = request.POST.get("text_answer")

        # TODO: Save StudentAnswer here

        if next_question:
            return redirect("exams:take_question", exam.id, next_question.id)
        else:
            return redirect("exams:exam_detail", exam.id)

    return render(request, "exams/take_question.html", {
        "exam": exam,
        "question": question,
        "choices": question.choices.all(),
    })



@login_required
def submit_answer(request, exam_id, question_id):
    if request.method != "POST":
        return redirect("exams:take_question", exam_id=exam_id, order=1)

    question = get_object_or_404(Question, id=question_id)

    StudentAnswer.objects.update_or_create(
        student=request.user,
        question=question,
        defaults={
            "choice_id": request.POST.get("choice"),
            "text_answer": request.POST.get("text_answer")
        }
    )

    next_q = Question.objects.filter(exam_id=exam_id, order__gt=question.order).order_by("order").first()

    if next_q:
        return redirect("exams:take_question", exam_id=exam_id, order=next_q.order)
    else:
        return redirect("exams:finish_exam", pk=exam_id)


@login_required
def finish_exam(request, pk):
    exam = get_object_or_404(Exam, pk=pk)

    correct = StudentAnswer.objects.filter(
        student=request.user,
        question__exam=exam,
        choice__is_correct=True
    ).count()

    ExamResult.objects.update_or_create(
        student=request.user,
        exam=exam,
        defaults={"score": correct}
    )

    return render(request, "exams/finished.html", {"exam": exam, "score": correct})
