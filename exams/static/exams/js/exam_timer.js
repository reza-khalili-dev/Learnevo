document.addEventListener("DOMContentLoaded", function () {
    const timerEl = document.getElementById("timer");
    if (!timerEl) return;

    let timeLeft = parseInt(timerEl.dataset.time); 
    const examId = timerEl.dataset.exam;           

    const countdown = setInterval(() => {
        if (timeLeft <= 0) {
            clearInterval(countdown);
            alert("Time is up! The exam will be submitted automatically.");
            window.location.href = `/exams/${examId}/finish/`;
        } else {
            let minutes = Math.floor(timeLeft / 60);
            let seconds = timeLeft % 60;
            timerEl.textContent = `${minutes}:${seconds.toString().padStart(2, "0")}`;
            timeLeft--;
        }
    }, 1000);
});
