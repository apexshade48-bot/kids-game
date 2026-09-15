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
    review: document.getElementById("fluency-review"),
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

  function askTeacher(mistake, box, btn) {
    btn.disabled = true;
    box.classList.remove("hidden");
    box.textContent = "🦉 Thinking…";
    fetch("/api/teacher", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: JSON.stringify({
        word: mistake.answer,
        text:
          'Explain to a small child why the sentence "' +
          mistake.phrase +
          '" uses the word "' +
          mistake.answer +
          '" and not "' +
          (mistake.chosen || "") +
          '". Keep it very short and simple.',
      }),
    })
      .then(function (res) {
        return res.json();
      })
      .then(function (data) {
        box.textContent = "🦉 " + ((data && (data.reply || data.error)) || "Try again in a moment.");
      })
      .catch(function () {
        box.textContent = "🦉 Teacher is asleep right now. Try again later.";
      })
      .then(function () {
        btn.disabled = false;
      });
  }

  function renderReview(mistakes) {
    if (!els.review) return;
    if (!mistakes || !mistakes.length) {
      els.review.classList.add("hidden");
      els.review.innerHTML = "";
      return;
    }
    els.review.innerHTML = "";
    els.review.classList.remove("hidden");
    mistakes.forEach(function (m) {
      const card = document.createElement("div");
      card.className = "fluency-mistake";

      const sentence = document.createElement("p");
      sentence.className = "fluency-sentence";
      sentence.textContent = m.phrase || "";
      card.appendChild(sentence);

      const said = document.createElement("p");
      said.innerHTML =
        'You said <span class="fluency-wrong">"' +
        (m.chosen || "—") +
        '"</span> — the right word is <span class="fluency-right">"' +
        m.answer +
        '"</span>.';
      card.appendChild(said);

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn btn-ghost btn-small";
      btn.textContent = "🦉 Ask Teacher";

      const replyBox = document.createElement("p");
      replyBox.className = "fluency-teacher-reply hidden";

      btn.addEventListener("click", function () {
        askTeacher(m, replyBox, btn);
      });

      card.appendChild(btn);
      card.appendChild(replyBox);
      els.review.appendChild(card);
    });
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
        els.doneTitle.textContent = "New level unlocked!";
        els.summary.textContent =
          "Perfect score — " +
          data.correct +
          "/" +
          data.total +
          "! You earned the Fluent badge. Your English is getting better every day — keep it up!";
        if (sfx && sfx.win) sfx.win();
        renderReview(null);
      } else {
        els.doneEmoji.textContent = "📚";
        els.doneTitle.textContent = "Not this time";
        els.summary.textContent =
          "You got " + data.correct + "/" + data.total + " right. You need a perfect score to pass — check what went wrong below, then try again soon.";
        renderReview(data.mistakes);
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
