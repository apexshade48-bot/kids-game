(function () {
  const root = document.getElementById("fluency-root");
  if (!root) return;

  const submitUrl = root.dataset.submitUrl || "/api/fluently/submit";
  let questions = [];
  try {
    questions = JSON.parse(root.dataset.questions || "[]");
  } catch (e) {
    questions = [];
  }

  const sfx = window.WordStarsSFX || null;

  const els = {
    progress: document.getElementById("fluency-progress"),
    panel: document.getElementById("fluency-panel"),
    done: document.getElementById("fluency-done"),
    phrase: document.getElementById("fluency-phrase"),
    choices: document.getElementById("fluency-choices"),
    feedback: document.getElementById("fluency-feedback"),
    summary: document.getElementById("fluency-summary"),
    doneTitle: document.getElementById("fluency-done-title"),
    doneEmoji: document.getElementById("fluency-done-emoji"),
  };

  let index = 0;
  let busy = false;
  const answers = [];

  function current() {
    return questions[index] || null;
  }

  function showQuestion() {
    const q = current();
    if (!q) {
      submitTest();
      return;
    }
    busy = false;
    els.feedback.textContent = "";
    els.feedback.className = "feedback";
    els.progress.textContent = index + 1 + " / " + questions.length;
    els.phrase.textContent = q.display || "";

    els.choices.innerHTML = "";
    (q.choices || []).forEach(function (choice) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "quiz-choice quiz-word-btn";
      btn.textContent = String(choice);
      btn.addEventListener("click", function () {
        pickAnswer(choice, btn);
      });
      els.choices.appendChild(btn);
    });
  }

  function pickAnswer(choice, btn) {
    if (busy) return;
    busy = true;
    answers.push(choice);

    const buttons = els.choices.querySelectorAll(".quiz-choice");
    buttons.forEach(function (b) {
      b.disabled = true;
    });
    if (btn) btn.classList.add("is-correct");

    window.setTimeout(function () {
      index += 1;
      showQuestion();
    }, 350);
  }

  async function parseJsonResponse(res) {
    const text = await res.text();
    try {
      return text ? JSON.parse(text) : {};
    } catch (e) {
      if (res.status === 401 || res.redirected || /<!DOCTYPE|<html/i.test(text)) {
        throw new Error("Session expired — please log in again.");
      }
      throw new Error("Server error while grading the test.");
    }
  }

  async function submitTest() {
    els.panel.classList.add("hidden");
    els.done.classList.remove("hidden");
    els.summary.textContent = "Grading your answers…";
    try {
      const res = await fetch(submitUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
        body: JSON.stringify({ answers: answers }),
      });
      const data = await parseJsonResponse(res);
      if (!res.ok || !data.ok) {
        els.doneEmoji.textContent = "😕";
        els.doneTitle.textContent = "Could not grade test";
        els.summary.textContent = (data && data.error) || "Something went wrong.";
        return;
      }
      if (data.passed) {
        els.doneEmoji.textContent = "🎓";
        els.doneTitle.textContent = "You passed!";
        els.summary.textContent =
          "Perfect score — " + data.correct + "/" + data.total + "! You earned the Fluent badge.";
        if (sfx && sfx.win) sfx.win();
      } else {
        els.doneEmoji.textContent = "📚";
        els.doneTitle.textContent = "Not this time";
        els.summary.textContent =
          "You got " + data.correct + "/" + data.total + " right. You need a perfect score to pass — try again soon.";
      }
    } catch (e) {
      els.doneEmoji.textContent = "😕";
      els.doneTitle.textContent = "Could not grade test";
      els.summary.textContent = (e && e.message) || "Something went wrong.";
    }
  }

  if (!questions.length) {
    els.feedback.textContent = "No test questions — try again later.";
    els.feedback.className = "feedback bad";
    return;
  }

  showQuestion();
})();
