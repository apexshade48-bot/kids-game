(function () {
  const root = document.getElementById("battle-root");
  if (!root) return;

  const sfx = window.WordStarsSFX || null;
  let words = [];
  try {
    words = JSON.parse(root.dataset.words || "[]");
  } catch (e) {
    words = [];
  }

  let p1 = root.dataset.p1 || "P1";
  let p2 = root.dataset.p2 || "P2";
  let turn = parseInt(root.dataset.turn, 10) || 1;
  let index = parseInt(root.dataset.index, 10) || 0;
  let total = parseInt(root.dataset.total, 10) || words.length;
  let p1Score = parseInt(root.dataset.p1Score, 10) || 0;
  let p2Score = parseInt(root.dataset.p2Score, 10) || 0;
  let done = root.dataset.done === "1";
  const answerUrl = root.dataset.answerUrl || "/api/battle/answer";
  const cancelUrl = root.dataset.cancelUrl || "/api/battle/cancel";
  let busy = false;

  const els = {
    progress: document.getElementById("battle-progress"),
    turnBanner: document.getElementById("turn-banner"),
    hint: document.getElementById("battle-hint"),
    word: document.getElementById("battle-word"),
    input: document.getElementById("battle-input"),
    feedback: document.getElementById("battle-feedback"),
    scoreP1: document.getElementById("score-p1"),
    scoreP2: document.getElementById("score-p2"),
    cardP1: document.getElementById("card-p1"),
    cardP2: document.getElementById("card-p2"),
    playPanel: document.getElementById("battle-play-panel"),
    donePanel: document.getElementById("battle-done"),
    doneTitle: document.getElementById("battle-done-title"),
    doneSummary: document.getElementById("battle-done-summary"),
    keyboard: document.getElementById("battle-keyboard"),
    btnCheck: document.getElementById("btn-battle-check"),
    btnClear: document.getElementById("btn-battle-clear"),
    btnQuit: document.getElementById("btn-battle-quit"),
  };

  function currentWord() {
    return words[index] || null;
  }

  function setTyped(v) {
    if (!els.input) return;
    els.input.value = String(v || "")
      .toLowerCase()
      .replace(/[^a-z]/g, "")
      .slice(0, 16);
  }

  function updateChrome() {
    if (els.progress) {
      els.progress.textContent =
        Math.min(index + 1, total) + " / " + total;
    }
    if (els.scoreP1) els.scoreP1.textContent = p1Score;
    if (els.scoreP2) els.scoreP2.textContent = p2Score;
    if (els.cardP1) els.cardP1.classList.toggle("is-turn", !done && turn === 1);
    if (els.cardP2) els.cardP2.classList.toggle("is-turn", !done && turn === 2);
    const name = turn === 1 ? p1 : p2;
    if (els.turnBanner) {
      els.turnBanner.textContent = done ? "Finished!" : name + "'s turn!";
    }
  }

  function showWord() {
    const item = currentWord();
    if (!item || done) {
      return;
    }
    if (els.hint) els.hint.textContent = item.hint || "✨";
    if (els.word) els.word.textContent = item.word;
    setTyped("");
    if (els.feedback) {
      els.feedback.textContent = "";
      els.feedback.className = "feedback";
    }
    updateChrome();
    if (els.input) els.input.focus({ preventScroll: true });
  }

  function buildKeyboard() {
    if (!els.keyboard) return;
    els.keyboard.innerHTML = "";
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").forEach(function (letter) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "key";
      btn.textContent = letter;
      btn.addEventListener("click", function () {
        if (busy || done) return;
        setTyped((els.input.value || "") + letter.toLowerCase());
      });
      els.keyboard.appendChild(btn);
    });
  }

  function showDone(data) {
    done = true;
    if (els.playPanel) els.playPanel.classList.add("hidden");
    if (els.donePanel) els.donePanel.classList.remove("hidden");
    updateChrome();
    let title = "Battle over!";
    let summary =
      p1 +
      " " +
      p1Score +
      " — " +
      p2Score +
      " " +
      p2;
    if (data) {
      if (data.winner === "p1") {
        title = "🏆 " + (data.winner_name || p1) + " wins!";
        if (data.reward) summary += "  ·  Host +" + data.reward + " 🪙";
      } else if (data.winner === "p2") {
        title = "🏆 " + (data.winner_name || p2) + " wins!";
      } else if (data.winner === "draw") {
        title = "🤝 Draw!";
        if (data.reward) summary += "  ·  Host +" + data.reward + " 🪙";
      }
    }
    if (els.doneTitle) els.doneTitle.textContent = title;
    if (els.doneSummary) els.doneSummary.textContent = summary;
    if (sfx && sfx.win) sfx.win();
  }

  async function submitAnswer() {
    if (busy || done) return;
    const answer = (els.input && els.input.value) || "";
    if (!answer.trim()) {
      if (els.feedback) {
        els.feedback.textContent = "Type the word first!";
        els.feedback.className = "feedback bad";
      }
      return;
    }
    busy = true;
    if (els.btnCheck) els.btnCheck.disabled = true;
    try {
      const res = await fetch(answerUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
        body: JSON.stringify({ answer: answer }),
      });
      const text = await res.text();
      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch (e) {
        throw new Error("Server error");
      }
      if (!res.ok) throw new Error(data.error || "Failed");

      p1Score = data.p1_score;
      p2Score = data.p2_score;
      turn = data.turn;
      index = data.index;
      total = data.total;

      if (data.correct) {
        if (els.feedback) {
          els.feedback.textContent = "Correct! ✓";
          els.feedback.className = "feedback ok";
        }
        if (sfx && sfx.correct) sfx.correct();
      } else {
        if (els.feedback) {
          els.feedback.textContent =
            'Not quite — it was "' + (data.want || "") + '"';
          els.feedback.className = "feedback bad";
        }
        if (sfx && sfx.wrong) sfx.wrong();
      }

      updateChrome();

      setTimeout(function () {
        busy = false;
        if (els.btnCheck) els.btnCheck.disabled = false;
        if (data.done) {
          showDone(data);
        } else {
          if (data.next) {
            words[index] = data.next;
          }
          showWord();
        }
      }, 900);
    } catch (e) {
      busy = false;
      if (els.btnCheck) els.btnCheck.disabled = false;
      if (els.feedback) {
        els.feedback.textContent = e.message || "Error";
        els.feedback.className = "feedback bad";
      }
    }
  }

  if (els.btnCheck) {
    els.btnCheck.addEventListener("click", submitAnswer);
  }
  if (els.btnClear) {
    els.btnClear.addEventListener("click", function () {
      if (busy) return;
      setTyped("");
    });
  }
  if (els.input) {
    els.input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        submitAnswer();
      }
    });
  }
  if (els.btnQuit) {
    els.btnQuit.addEventListener("click", function (e) {
      e.preventDefault();
      fetch(cancelUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-Requested-With": "XMLHttpRequest" },
      }).finally(function () {
        window.location.href = root.dataset.homeUrl || "/home";
      });
    });
  }

  buildKeyboard();
  if (done) {
    showDone({
      winner: root.dataset.winner ? "p1" : null,
      winner_name: root.dataset.winner,
    });
  } else {
    showWord();
  }
})();
