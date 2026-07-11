(function () {
  const root = document.getElementById("game-root");
  if (!root) return;

  const mode = root.dataset.mode;
  const pointsPerWord = parseInt(root.dataset.points, 10) || 10;
  const scoreUrl = root.dataset.scoreUrl;
  let words = [];
  try {
    words = JSON.parse(root.dataset.words || "[]");
  } catch (e) {
    words = [];
  }

  const els = {
    progress: document.getElementById("progress"),
    roundScore: document.getElementById("round-score"),
    playPanel: document.getElementById("play-panel"),
    donePanel: document.getElementById("done-panel"),
    wordHint: document.getElementById("word-hint"),
    targetWord: document.getElementById("target-word"),
    typed: document.getElementById("typed-display"),
    mobileInput: document.getElementById("mobile-input"),
    feedback: document.getElementById("feedback"),
    voiceStatus: document.getElementById("voice-status"),
    keyboard: document.getElementById("keyboard"),
    btnMic: document.getElementById("btn-mic"),
    btnCheck: document.getElementById("btn-check"),
    btnClear: document.getElementById("btn-clear"),
    doneSummary: document.getElementById("done-summary"),
  };

  let index = 0;
  let typed = "";
  let roundPoints = 0;
  let roundCoins = 0;
  let correctCount = 0;
  let busy = false;
  let recognition = null;
  let listening = false;

  function current() {
    return words[index] || null;
  }

  function normalize(s) {
    return String(s || "")
      .toLowerCase()
      .replace(/[^a-z]/g, "")
      .trim();
  }

  function setTyped(value) {
    typed = value.toLowerCase().replace(/[^a-z]/g, "").slice(0, 12);
    if (els.typed) els.typed.textContent = typed;
    if (els.mobileInput && els.mobileInput.value !== typed) {
      els.mobileInput.value = typed;
    }
  }

  function showWord() {
    const item = current();
    if (!item) {
      finishRound();
      return;
    }
    typed = "";
    busy = false;
    if (els.typed) els.typed.textContent = "";
    if (els.mobileInput) els.mobileInput.value = "";
    els.feedback.textContent = "";
    els.feedback.className = "feedback";
    els.voiceStatus.textContent = "";
    els.wordHint.textContent = item.hint || "✨";
    els.targetWord.textContent = item.word;
    els.progress.textContent = index + 1 + " / " + words.length;
    els.roundScore.textContent = "⭐ " + roundPoints;
  }

  function bindKey(btn, letter) {
    function press() {
      if (busy) return;
      setTyped(typed + letter.toLowerCase());
      els.feedback.textContent = "";
      if (els.mobileInput) els.mobileInput.focus({ preventScroll: true });
    }
    btn.addEventListener("click", press);
    btn.addEventListener("touchend", function (e) {
      e.preventDefault();
      press();
    });
  }

  function buildKeyboard() {
    const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
    els.keyboard.innerHTML = "";
    letters.forEach(function (letter) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "key";
      btn.textContent = letter;
      bindKey(btn, letter);
      els.keyboard.appendChild(btn);
    });
  }

  async function awardPoints() {
    try {
      const res = await fetch(scoreUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ mode: mode, points: pointsPerWord }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      return !!data.ok;
    } catch (e) {
      els.feedback.className = "feedback bad";
      els.feedback.textContent = "Lost connection — check Wi‑Fi and try again.";
      return false;
    }
  }

  async function onCorrect(source) {
    if (busy) return;
    busy = true;
    correctCount += 1;
    roundPoints += pointsPerWord;
    roundCoins += pointsPerWord;
    els.roundScore.textContent = "⭐ " + roundPoints;
    els.feedback.textContent =
      source === "voice"
        ? "Great speaking! 🎉 +" + pointsPerWord + " 🪙"
        : "Yes! +" + pointsPerWord + " ⭐ +" + pointsPerWord + " 🪙";
    els.feedback.className = "feedback ok";
    els.targetWord.classList.add("celebrate");
    await awardPoints();

    setTimeout(function () {
      els.targetWord.classList.remove("celebrate");
      index += 1;
      if (index >= words.length) {
        finishRound();
      } else {
        showWord();
      }
    }, 900);
  }

  function onWrong(heard) {
    els.feedback.className = "feedback bad";
    if (heard) {
      els.feedback.textContent = 'Almost! You said "' + heard + '". Try again!';
    } else {
      els.feedback.textContent = "Not yet — try again!";
    }
  }

  async function checkAnswer(answer, source) {
    const item = current();
    if (!item || busy) return;
    const want = normalize(item.word);
    const got = normalize(answer);
    if (!got) {
      els.feedback.textContent = "Type or say the word first!";
      els.feedback.className = "feedback bad";
      return;
    }
    if (got === want) {
      await onCorrect(source || "type");
    } else {
      onWrong(source === "voice" ? answer : null);
    }
  }

  function finishRound() {
    els.playPanel.classList.add("hidden");
    els.donePanel.classList.remove("hidden");
    els.doneSummary.textContent =
      "You got " +
      correctCount +
      " of " +
      words.length +
      " words. +" +
      roundPoints +
      " stars and +" +
      roundCoins +
      " coins!";
  }

  function setupSpeech() {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
      (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

    if (!SpeechRecognition) {
      els.btnMic.disabled = true;
      els.btnMic.classList.add("unsupported");
      els.voiceStatus.textContent = isIOS
        ? "On iPad/iPhone, tap the box and type — or use the letter keys."
        : "Voice not available — tap the box or use letter keys.";
      return;
    }

    if (!window.isSecureContext && location.hostname !== "localhost") {
      els.voiceStatus.textContent =
        "Voice needs a secure link on some devices — typing works great!";
    }

    recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 3;
    recognition.continuous = false;

    recognition.onstart = function () {
      listening = true;
      els.btnMic.classList.add("listening");
      els.btnMic.textContent = "🔴 Listening…";
      els.voiceStatus.textContent = "Listening… say the word!";
    };

    recognition.onend = function () {
      listening = false;
      els.btnMic.classList.remove("listening");
      els.btnMic.textContent = "🎤 Say it";
    };

    recognition.onerror = function (event) {
      listening = false;
      els.btnMic.classList.remove("listening");
      els.btnMic.textContent = "🎤 Say it";
      if (event.error === "not-allowed") {
        els.voiceStatus.textContent =
          "Mic blocked — tap the answer box or use letter keys.";
      } else if (event.error !== "aborted") {
        els.voiceStatus.textContent = "Could not hear — try typing!";
      }
    };

    recognition.onresult = function (event) {
      const results = event.results[0];
      let best = "";
      const item = current();
      const want = item ? normalize(item.word) : "";

      for (let i = 0; i < results.length; i++) {
        const transcript = results[i].transcript || "";
        const n = normalize(transcript);
        if (!best) best = transcript;
        if (n === want) {
          setTyped(want);
          checkAnswer(want, "voice");
          return;
        }
      }
      setTyped(normalize(best));
      checkAnswer(best, "voice");
    };

    els.btnMic.addEventListener("click", function () {
      if (busy) return;
      if (!recognition) return;
      if (listening) {
        try {
          recognition.stop();
        } catch (e) {}
        return;
      }
      els.feedback.textContent = "";
      try {
        recognition.start();
      } catch (e) {
        els.voiceStatus.textContent = "Mic busy — try again or type.";
      }
    });
  }

  if (els.mobileInput) {
    els.mobileInput.addEventListener("input", function () {
      if (busy) return;
      setTyped(els.mobileInput.value);
      els.feedback.textContent = "";
    });
    els.mobileInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        checkAnswer(typed, "type");
      }
    });
  }

  els.btnClear.addEventListener("click", function () {
    if (busy) return;
    setTyped("");
    els.feedback.textContent = "";
    if (els.mobileInput) els.mobileInput.focus({ preventScroll: true });
  });

  els.btnCheck.addEventListener("click", function () {
    checkAnswer(typed, "type");
  });

  document.addEventListener("keydown", function (e) {
    if (busy || (els.donePanel && !els.donePanel.classList.contains("hidden"))) return;
    if (document.activeElement === els.mobileInput) return;
    if (e.key === "Enter") {
      e.preventDefault();
      checkAnswer(typed, "type");
      return;
    }
    if (e.key === "Backspace") {
      e.preventDefault();
      setTyped(typed.slice(0, -1));
      return;
    }
    if (/^[a-zA-Z]$/.test(e.key)) {
      setTyped(typed + e.key.toLowerCase());
    }
  });

  buildKeyboard();
  setupSpeech();
  showWord();
})();