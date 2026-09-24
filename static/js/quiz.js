(function () {
  const root = document.getElementById("quiz-root");
  if (!root) return;

  const mode = root.dataset.mode;
  const modeLabel = root.dataset.modeLabel || mode;
  const pointsPerWord = parseInt(root.dataset.points, 10) || 10;
  const quizKind = root.dataset.quizKind || "letter";
  const scoreUrl = root.dataset.scoreUrl || "/api/score";
  let questions = [];
  try {
    questions = JSON.parse(root.dataset.questions || "[]");
  } catch (e) {
    questions = [];
  }

  const sfx = window.WordStarsSFX || null;

  function ping(el, cls) {
    if (!el) return;
    el.classList.remove(cls);
    void el.offsetWidth;
    el.classList.add(cls);
  }

  function burst(host) {
    if (!host) return;
    var bits = ["⭐", "✨", "🎉", "💛"];
    var i;
    for (i = 0; i < 8; i++) {
      (function (n) {
        var s = document.createElement("span");
        s.className = "fx-star";
        s.textContent = bits[n % bits.length];
        s.style.setProperty("--dx", Math.round(Math.random() * 180 - 90) + "px");
        s.style.setProperty("--dy", Math.round(-24 - Math.random() * 90) + "px");
        s.style.setProperty("--rot", Math.round(Math.random() * 70 - 35) + "deg");
        host.appendChild(s);
        window.setTimeout(function () {
          if (s.parentNode) s.parentNode.removeChild(s);
        }, 850);
      })(i);
    }
  }

  async function parseJsonResponse(res) {
    const text = await res.text();
    try {
      return text ? JSON.parse(text) : {};
    } catch (e) {
      if (res.status === 401 || res.redirected || /<!DOCTYPE|<html/i.test(text)) {
        throw new Error("Session expired — please log in again.");
      }
      throw new Error("Server error while saving score.");
    }
  }

  const els = {
    progress: document.getElementById("quiz-progress"),
    progressBar: document.getElementById("quiz-progress-bar"),
    progressCaption: document.getElementById("quiz-progress-caption"),
    score: document.getElementById("quiz-score"),
    panel: document.getElementById("quiz-panel"),
    done: document.getElementById("quiz-done"),
    doneEmoji: document.getElementById("quiz-done-emoji"),
    doneTitle: document.getElementById("quiz-done-title"),
    hint: document.getElementById("quiz-hint"),
    blankWord: document.getElementById("quiz-blank-word"),
    choices: document.getElementById("quiz-choices"),
    feedback: document.getElementById("quiz-feedback"),
    summary: document.getElementById("quiz-summary"),
    prompt: document.getElementById("quiz-prompt"),
  };

  let index = 0;
  let roundPoints = 0;
  let roundCoins = 0;
  let correctCount = 0;
  let busy = false;

  function current() {
    return questions[index] || null;
  }

  function updateProgress(completed) {
    var done = typeof completed === "number" ? completed : index;
    var total = questions.length;
    var percent = total ? Math.min(100, Math.round((done / total) * 100)) : 0;
    if (els.progressBar) {
      els.progressBar.style.width = percent + "%";
      els.progressBar.setAttribute("aria-valuenow", String(done));
      els.progressBar.setAttribute("aria-valuetext", done + " of " + total + " questions complete");
    }
    if (els.progressCaption) {
      els.progressCaption.textContent = done + " of " + total + " complete";
    }
  }

  function isPicture() {
    const q = current();
    return quizKind === "picture" || (q && q.quiz_type === "picture");
  }

  function renderBlankWord(q, filledLetter) {
    if (!els.blankWord) return;
    if (isPicture()) {
      els.blankWord.innerHTML = "";
      els.blankWord.classList.add("hidden");
      return;
    }
    els.blankWord.classList.remove("hidden");
    els.blankWord.innerHTML = "";
    const display = q.display || [];
    const blankIndex =
      typeof q.blank_index === "number" ? q.blank_index : display.indexOf("");

    display.forEach(function (ch, i) {
      const span = document.createElement("span");
      if (i === blankIndex) {
        span.className =
          "quiz-letter quiz-letter-blank" + (filledLetter ? " is-filled" : "");
        span.textContent = filledLetter
          ? String(filledLetter).toUpperCase()
          : "_";
      } else {
        span.className = "quiz-letter";
        span.textContent = String(ch || "").toUpperCase();
      }
      els.blankWord.appendChild(span);
    });
  }

  function showQuestion() {
    const q = current();
    if (!q) {
      finishQuiz();
      return;
    }
    busy = false;
    els.feedback.textContent = "";
    els.feedback.className = "feedback";
    els.hint.textContent = q.hint || "✨";
    ping(els.hint, "word-in");
    ping(els.blankWord, "word-in");
    ping(els.choices, "choices-in");
    els.progress.textContent = index + 1 + " / " + questions.length;
    updateProgress();
    els.score.textContent = "⭐ " + roundPoints;

    if (els.prompt) {
      if (mode === "letters" && isPicture()) {
        els.prompt.textContent = "Which letter matches the picture?";
      } else if (isPicture()) {
        els.prompt.textContent = "Which word matches the picture?";
      } else if (mode === "letters") {
        els.prompt.textContent = "Tap the first letter of the word!";
      } else {
        els.prompt.textContent = "One letter is missing — tap the right letter!";
      }
    }

    renderBlankWord(q, null);

    els.choices.className = isPicture()
      ? "quiz-choices quiz-word-choices"
      : "quiz-choices quiz-letter-choices";

    els.choices.innerHTML = "";
    (q.choices || []).forEach(function (choice) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = isPicture()
        ? "quiz-choice quiz-word-btn"
        : "quiz-choice quiz-letter-btn";
      btn.textContent =
        isPicture() && mode !== "letters"
          ? String(choice)
          : String(choice).toUpperCase();
      btn.setAttribute(
        "aria-label",
        isPicture() ? "Choose " + String(choice) : "Choose letter " + String(choice)
      );
      btn.dataset.answer = String(choice).toLowerCase();
      btn.addEventListener("click", function () {
        pickAnswer(choice, btn);
      });
      els.choices.appendChild(btn);
    });
  }

  async function awardPoints(answer) {
    try {
      const res = await fetch(scoreUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
        body: JSON.stringify({
          mode: mode,
          points: pointsPerWord,
          word: (current() && current().word) || "",
          answer: answer || (current() && current().word) || "",
        }),
      });
      const data = await parseJsonResponse(res);
      if (!res.ok) {
        return {
          ok: false,
          error: (data && data.error) || "Could not save score — try again.",
          status: res.status,
        };
      }
      if (!data || data.ok !== true) {
        return {
          ok: false,
          error: (data && data.error) || "Could not save score — try again.",
          data: data || {},
          status: res.status,
        };
      }
      if (typeof data.coins === "number") {
        document.querySelectorAll(".top-coins").forEach(function (el) {
          el.textContent = "🪙 " + data.coins;
        });
        var quizHomeCoins = document.getElementById("coin-balance");
        if (quizHomeCoins) quizHomeCoins.textContent = data.coins;
      }
      return { ok: true, data: data, status: res.status };
    } catch (e) {
      var msg = (e && e.message) || "";
      if (/failed to fetch|networkerror|load failed/i.test(msg)) {
        msg = "Cannot reach the server. Start with python app.py, then reload.";
      }
      return {
        ok: false,
        error: msg || "Could not save score.",
        status: 0,
      };
    }
  }

  function retryQuestion(q, want) {
    if (current() !== q) return;
    els.choices.querySelectorAll(".quiz-choice").forEach(function (b) {
      b.disabled = false;
      b.classList.remove("is-wrong");
      if (String(b.dataset.answer || "").toLowerCase() === want) {
        b.classList.add("is-correct");
      }
    });
    busy = false;
    els.feedback.className = "feedback bad";
    els.feedback.textContent =
      "Almost! The answer is " +
      String(q.word || "").toUpperCase() +
      ". Tap the green answer to continue.";
  }

  async function pickAnswer(choice, btn) {
    const q = current();
    if (!q || busy) return;
    busy = true;

    const want = isPicture()
      ? String(q.word || "").toLowerCase()
      : String(q.missing || "").toLowerCase();
    const got = String(choice || "").toLowerCase();
    const fullWord = String(q.word || "").toUpperCase();
    const correct = got === want;

    const buttons = els.choices.querySelectorAll(".quiz-choice");
    buttons.forEach(function (b) {
      b.disabled = true;
      if (String(b.dataset.answer || "").toLowerCase() === want) {
        b.classList.add("is-correct");
      }
    });

    if (!correct) {
      if (!isPicture()) renderBlankWord(q, want);
      els.feedback.textContent = "Almost! The answer is " + fullWord + ".";
      els.feedback.className = "feedback bad";
      if (btn) btn.classList.add("is-wrong");
      ping(els.hint, "shake");
      ping(els.choices, "shake");
      if (window.WordStarsStop) {
        window.WordStarsStop.reportMistake(q.word || "", got);
      }
      if (sfx && sfx.wrong) sfx.wrong();
      window.setTimeout(function () {
        retryQuestion(q, want);
      }, 1100);
      return;
    }

    if (!isPicture()) renderBlankWord(q, got);
    els.feedback.textContent = "Saving your star…";
    els.feedback.className = "feedback";
    // Picture quiz choices are already the full word; the letter quiz only
    // asks for the missing letter, so the confirmed full word is what
    // proves the answer (matches what the server's round expects).
    const saved = await awardPoints(isPicture() ? choice : q.word || "");
    if (!saved.ok) {
      els.choices.querySelectorAll(".quiz-choice").forEach(function (b) {
        b.disabled = false;
      });
      busy = false;
      els.feedback.className = "feedback bad";
      if (saved.status === 429) {
        els.feedback.textContent = "Just a moment — tap the green answer again.";
      } else {
        els.feedback.textContent = saved.error + " Tap the green answer to try saving again.";
      }
      return;
    }

    correctCount += 1;
    roundPoints += pointsPerWord;
    roundCoins += pointsPerWord;
    if (saved.data && saved.data.daily_bonus) {
      roundCoins += saved.data.daily_bonus;
    }
    els.score.textContent = "⭐ " + roundPoints;
    els.feedback.textContent =
      "Yes! " +
      fullWord +
      "  +" +
      pointsPerWord +
      " ⭐ +" +
      pointsPerWord +
      " 🪙";
    if (saved.data && saved.data.daily_bonus) {
      els.feedback.textContent += " 🌞 +" + saved.data.daily_bonus + " bonus!";
    }
    els.feedback.className = "feedback ok";
    if (btn) btn.classList.add("is-correct");
    ping(els.hint, "celebrate");
    ping(els.score, "score-pop");
    ping(els.feedback, "pop-in");
    var stage = document.querySelector(".word-stage");
    if (stage) {
      stage.classList.add("is-win");
      burst(stage);
      window.setTimeout(function () {
        stage.classList.remove("is-win");
      }, 700);
    }
    if (sfx && sfx.correct) sfx.correct();

    function goNext() {
      els.hint.classList.remove("celebrate");
      if (els.score) els.score.classList.remove("score-pop");
      index += 1;
      if (index >= questions.length) {
        finishQuiz();
      } else {
        showQuestion();
      }
    }
    window.setTimeout(goNext, 650);
  }

  function finishQuiz() {
    updateProgress(questions.length);
    els.panel.classList.add("hidden");
    els.done.classList.remove("hidden");
    ping(els.done, "win-in");
    burst(els.done);
    if (sfx && sfx.win) sfx.win();
    const perfect = questions.length > 0 && correctCount === questions.length;
    if (perfect) {
      if (els.doneEmoji) els.doneEmoji.textContent = "🌟";
      if (els.doneTitle) els.doneTitle.textContent = "Perfect round!";
    } else {
      if (els.doneEmoji) els.doneEmoji.textContent = "🧠";
      if (els.doneTitle) els.doneTitle.textContent = "Quiz complete";
    }
    els.summary.textContent =
      "You got " +
      correctCount +
      " of " +
      questions.length +
      " right. +" +
      roundPoints +
      " stars and +" +
      roundCoins +
      " coins!" +
      (perfect
        ? " All correct in " + modeLabel + " — your English is getting better every day!"
        : "");
  }

  document.addEventListener("keydown", function (e) {
    if (busy || !els.done.classList.contains("hidden")) return;
    if (isPicture()) return;
    if (!/^[a-zA-Z]$/.test(e.key)) return;
    const letter = e.key.toLowerCase();
    const btn = els.choices.querySelector(
      '.quiz-choice[data-answer="' + letter + '"]'
    );
    if (btn && !btn.disabled) {
      pickAnswer(letter, btn);
    }
  });

  if (!questions.length) {
    els.feedback.textContent = "No quiz questions — try again later.";
    els.feedback.className = "feedback bad";
    return;
  }

  showQuestion();
})();
