(function () {
  const root = document.getElementById("game-root");
  if (!root) return;

  const mode = root.dataset.mode;
  const pointsPerWord = parseInt(root.dataset.points, 10) || 10;
  const scoreUrl = root.dataset.scoreUrl || "/api/score";
  const hintUrl = root.dataset.hintUrl || "/api/hint";
  const hintCost = parseInt(root.dataset.hintCost, 10) || 5;
  const sfx = window.WordStarsSFX || null;
  let words = [];
  try {
    words = JSON.parse(root.dataset.words || "[]");
  } catch (e) {
    words = [];
  }
  let hintUsedThisWord = false;

  async function parseJsonResponse(res) {
    const text = await res.text();
    try {
      return text ? JSON.parse(text) : {};
    } catch (e) {
      if (
        res.status === 401 ||
        res.redirected ||
        /<!DOCTYPE|<html/i.test(text)
      ) {
        throw new Error("Session expired — please log in again.");
      }
      throw new Error("Server error while saving score.");
    }
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
    btnHint: document.getElementById("btn-hint"),
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

  // Speech
  const SpeechRecognitionCtor =
    window.SpeechRecognition || window.webkitSpeechRecognition || null;
  let recognition = null;
  let listening = false;
  let voiceSupported = !!SpeechRecognitionCtor;
  let lastResultAt = 0;

  function current() {
    return words[index] || null;
  }

  function normalize(s) {
    // Collapse to letters only so "how are you" == "howareyou"
    return String(s || "")
      .toLowerCase()
      .replace(/[^a-z]/g, "")
      .trim();
  }

  const speakFocus = root.dataset.speakFocus === "1";
  const maxTyped = speakFocus ? 48 : 12;

  function cleanPhraseInput(value) {
    // Allow letters + spaces for Impossible phrases (e.g. "how are you")
    var s = String(value || "").toLowerCase().replace(/[^a-z\s]/g, "");
    // Collapse runs of spaces to a single space, but keep a trailing space while typing
    var trailing = /\s$/.test(s);
    s = s.replace(/\s+/g, " ").replace(/^\s+/, "");
    if (trailing && s.length > 0 && !/\s$/.test(s)) s += " ";
    return s.slice(0, maxTyped);
  }

  function setTyped(value) {
    if (speakFocus) {
      typed = cleanPhraseInput(value);
    } else {
      typed = String(value || "")
        .toLowerCase()
        .replace(/[^a-z]/g, "")
        .slice(0, maxTyped);
    }
    if (els.typed) els.typed.textContent = typed;
    if (els.mobileInput && els.mobileInput.value !== typed) {
      els.mobileInput.value = typed;
      // Keep caret at end after we rewrite value
      try {
        var len = typed.length;
        els.mobileInput.setSelectionRange(len, len);
      } catch (e) {}
    }
  }

  function setVoiceStatus(msg) {
    if (els.voiceStatus) els.voiceStatus.textContent = msg || "";
  }

  function setMicListening(on) {
    listening = !!on;
    if (!els.btnMic) return;
    if (on) {
      els.btnMic.classList.add("listening");
      els.btnMic.setAttribute("aria-pressed", "true");
      els.btnMic.textContent = "🔴 Listening…";
    } else {
      els.btnMic.classList.remove("listening");
      els.btnMic.setAttribute("aria-pressed", "false");
      els.btnMic.textContent = "🎤 Say it";
    }
  }

  function isSecureEnough() {
    if (window.isSecureContext) return true;
    const h = (location.hostname || "").toLowerCase();
    return h === "localhost" || h === "127.0.0.1" || h === "[::1]";
  }

  function showWord() {
    const item = current();
    if (!item) {
      finishRound();
      return;
    }
    hardStopMic();
    typed = "";
    busy = false;
    hintUsedThisWord = false;
    if (els.typed) els.typed.textContent = "";
    if (els.mobileInput) els.mobileInput.value = "";
    els.feedback.textContent = "";
    els.feedback.className = "feedback";
    els.wordHint.textContent = item.hint || "✨";
    els.targetWord.textContent = item.word;
    els.progress.textContent = index + 1 + " / " + words.length;
    els.roundScore.textContent = "⭐ " + roundPoints;
    if (els.btnHint) {
      els.btnHint.disabled = false;
      els.btnHint.textContent = "💡 Hint (" + hintCost + "🪙)";
    }
    if (voiceSupported) {
      setVoiceStatus("Tap 🎤 Say it, then speak the word.");
    }
  }

  function bindKey(btn, insert) {
    function press() {
      if (busy) return;
      if (insert === " ") {
        setTyped(typed + " ");
      } else {
        setTyped(typed + String(insert).toLowerCase());
      }
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
    // Space bar required for Impossible phrases ("good morning")
    if (speakFocus) {
      const space = document.createElement("button");
      space.type = "button";
      space.className = "key key-space";
      space.textContent = "Space";
      space.setAttribute("aria-label", "Space");
      bindKey(space, " ");
      els.keyboard.appendChild(space);
    }
  }

  async function awardPoints() {
    try {
      const res = await fetch(scoreUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
        body: JSON.stringify({ mode: mode, points: pointsPerWord }),
      });
      const data = await parseJsonResponse(res);
      if (!res.ok) {
        els.feedback.className = "feedback bad";
        els.feedback.textContent =
          (data && data.error) || "Could not save score — try again.";
        return false;
      }
      return !!data.ok;
    } catch (e) {
      els.feedback.className = "feedback bad";
      var msg = (e && e.message) || "";
      if (/failed to fetch|networkerror|load failed/i.test(msg)) {
        msg =
          "Cannot reach the server. Start with python app.py, then reload.";
      }
      els.feedback.textContent =
        msg || "Lost connection — check Wi‑Fi and try again.";
      return false;
    }
  }

  async function onCorrect(source) {
    if (busy) return;
    busy = true;
    hardStopMic();
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
    if (sfx && sfx.correct) sfx.correct();
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
    if (sfx && sfx.wrong) sfx.wrong();
    if (heard) {
      els.feedback.textContent = 'Almost! You said "' + heard + '". Try again!';
    } else {
      els.feedback.textContent = "Not yet — try again!";
    }
  }

  /** Match spoken text to target (kids often add extra words). */
  function speechMatches(answer, want) {
    const got = normalize(answer);
    if (!got || !want) return false;
    if (got === want) return true;

    const tokens = String(answer || "")
      .toLowerCase()
      .replace(/[^a-z\s]/g, " ")
      .split(/\s+/)
      .map(normalize)
      .filter(Boolean);

    if (tokens.indexOf(want) !== -1) return true;
    if (tokens.join("") === want) return true;

    // single letter names: "see" for C, "bee" for B, etc. not used
    // fuzzy: spoken contains target
    if (want.length >= 3 && got.indexOf(want) !== -1) return true;
    if (want.length >= 3 && want.indexOf(got) !== -1 && got.length >= want.length - 1)
      return true;

    return false;
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
    if (source === "voice" ? speechMatches(answer, want) : got === want) {
      setTyped(want);
      await onCorrect(source || "type");
    } else {
      onWrong(source === "voice" ? answer : null);
    }
  }

  function finishRound() {
    hardStopMic();
    els.playPanel.classList.add("hidden");
    els.donePanel.classList.remove("hidden");
    if (sfx && sfx.win) sfx.win();
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

  async function useHint() {
    if (busy || hintUsedThisWord) return;
    const item = current();
    if (!item) return;
    if (els.btnHint) els.btnHint.disabled = true;
    try {
      const res = await fetch(hintUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
        body: JSON.stringify({ mode: mode, word: item.word }),
      });
      const text = await res.text();
      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch (e) {
        throw new Error("Could not use hint — try again.");
      }
      if (!res.ok) {
        els.feedback.className = "feedback bad";
        els.feedback.textContent = data.error || "Hint failed.";
        if (els.btnHint) els.btnHint.disabled = false;
        return;
      }
      hintUsedThisWord = true;
      const letter = data.hint_letter || String(item.word)[0].toUpperCase();
      setTyped(letter.toLowerCase());
      els.feedback.className = "feedback ok";
      els.feedback.textContent =
        "Hint: starts with “" + letter + "” (−" + hintCost + " coins)";
      if (els.btnHint) els.btnHint.textContent = "💡 Used";
      if (sfx && sfx.click) sfx.click();
    } catch (e) {
      els.feedback.className = "feedback bad";
      els.feedback.textContent = (e && e.message) || "Hint failed.";
      if (els.btnHint) els.btnHint.disabled = false;
    }
  }

  /** Stop mic without async — safe anytime. */
  function hardStopMic() {
    const rec = recognition;
    recognition = null;
    listening = false;
    setMicListening(false);
    if (!rec) return;
    try {
      rec.onstart = null;
      rec.onresult = null;
      rec.onerror = null;
      rec.onend = null;
      rec.onspeechend = null;
      rec.onaudiostart = null;
      rec.abort();
    } catch (e) {
      try {
        rec.stop();
      } catch (e2) {}
    }
  }

  /**
   * Start listening. MUST be called directly from a click/tap handler
   * (no await before rec.start — browsers require a user gesture).
   */
  function startListeningFromGesture() {
    if (busy || !voiceSupported || !els.btnMic) return;

    // Toggle off if already listening
    if (listening || recognition) {
      hardStopMic();
      setVoiceStatus("Stopped. Tap 🎤 Say it to try again.");
      return;
    }

    if (!isSecureEnough()) {
      setVoiceStatus(
        "Voice needs localhost or HTTPS. On this PC use http://127.0.0.1:5000 — or type the word."
      );
      // Still try — some browsers allow it
    }

    const rec = new SpeechRecognitionCtor();
    recognition = rec;
    lastResultAt = 0;

    rec.lang = "en-US";
    rec.interimResults = true;
    rec.maxAlternatives = 5;
    rec.continuous = false;

    // Help Chrome prefer the target word when possible
    try {
      const item = current();
      const GrammarList =
        window.SpeechGrammarList || window.webkitSpeechGrammarList;
      if (GrammarList && item && item.word) {
        const list = new GrammarList();
        const grammar =
          "#JSGF V1.0; grammar words; public <word> = " +
          String(item.word).toLowerCase() +
          " ;";
        list.addFromString(grammar, 1);
        rec.grammars = list;
      }
    } catch (e) {}

    rec.onstart = function () {
      setMicListening(true);
      setVoiceStatus("Listening… say the word now!");
    };

    rec.onaudiostart = function () {
      setVoiceStatus("Mic on — say the word clearly!");
    };

    rec.onspeechend = function () {
      // End session so we get a final result faster
      try {
        rec.stop();
      } catch (e) {}
    };

    rec.onresult = function (event) {
      if (busy) return;
      lastResultAt = Date.now();
      const item = current();
      const want = item ? normalize(item.word) : "";
      let bestFinal = "";
      let bestAny = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        for (let j = 0; j < result.length; j++) {
          const transcript = (result[j] && result[j].transcript) || "";
          if (!transcript) continue;
          if (!bestAny) bestAny = transcript;
          if (result.isFinal && !bestFinal) bestFinal = transcript;

          if (want && speechMatches(transcript, want)) {
            setTyped(want);
            hardStopMic();
            setVoiceStatus("Heard it! ✓");
            checkAnswer(want, "voice");
            return;
          }
        }
      }

      // Live preview
      if (bestAny) {
        if (speakFocus) {
          setTyped(cleanPhraseInput(bestAny));
        } else {
          const live = normalize(bestAny);
          if (live) setTyped(live);
        }
        const last = event.results[event.results.length - 1];
        if (last && !last.isFinal) {
          setVoiceStatus('Hearing: "' + bestAny.trim() + '"…');
        }
      }

      // Final transcript
      if (event.results[event.results.length - 1].isFinal) {
        const finalText = bestFinal || bestAny;
        if (finalText) {
          if (speakFocus) {
            setTyped(cleanPhraseInput(finalText));
          } else {
            setTyped(normalize(finalText));
          }
          hardStopMic();
          setVoiceStatus('You said: "' + finalText.trim() + '"');
          checkAnswer(finalText, "voice");
        }
      }
    };

    rec.onerror = function (event) {
      const code = (event && event.error) || "";
      // Ignore aborted from our own hardStopMic
      if (code === "aborted") {
        setMicListening(false);
        recognition = null;
        return;
      }

      let msg = "Could not hear — tap Say it again or type.";
      if (code === "not-allowed" || code === "service-not-allowed") {
        if (!isSecureEnough()) {
          msg =
            "Mic blocked on this link. Open http://127.0.0.1:5000 on this PC (Chrome), allow mic, or type.";
        } else {
          msg =
            "Mic blocked. Click the lock icon → allow Microphone → try again.";
        }
      } else if (code === "no-speech") {
        msg = "No speech heard — tap Say it and speak louder.";
      } else if (code === "audio-capture") {
        msg = "No microphone found — use typing or letter keys.";
      } else if (code === "network") {
        msg = "Voice needs internet (Chrome). Check connection, then try again.";
      } else if (code === "busy") {
        msg = "Mic busy — wait 1 second, then tap Say it.";
      }

      setMicListening(false);
      recognition = null;
      setVoiceStatus(msg);
    };

    rec.onend = function () {
      // If Chrome ended without a result, show tip
      if (listening && Date.now() - lastResultAt > 400) {
        setVoiceStatus("Tap 🎤 Say it and try again.");
      }
      setMicListening(false);
      if (recognition === rec) recognition = null;
    };

    // CRITICAL: start() in the same user-gesture turn (no await above)
    try {
      rec.start();
      // Optimistic UI if onstart is slow
      setMicListening(true);
      setVoiceStatus("Starting mic… speak after the beep / red button.");
    } catch (err) {
      recognition = null;
      setMicListening(false);
      const name = (err && err.name) || "";
      if (name === "InvalidStateError") {
        // Already started — recreate once, still in gesture if sync
        try {
          hardStopMic();
          const rec2 = new SpeechRecognitionCtor();
          recognition = rec2;
          rec2.lang = "en-US";
          rec2.interimResults = true;
          rec2.maxAlternatives = 5;
          rec2.continuous = false;
          rec2.onresult = rec.onresult;
          rec2.onerror = rec.onerror;
          rec2.onend = rec.onend;
          rec2.onstart = rec.onstart;
          rec2.start();
          setMicListening(true);
          setVoiceStatus("Listening… say the word!");
          return;
        } catch (e2) {}
      }
      setVoiceStatus("Could not start mic — use Chrome/Edge, or type the word.");
    }
  }

  function setupSpeech() {
    if (!els.btnMic) return;

    if (!SpeechRecognitionCtor) {
      voiceSupported = false;
      els.btnMic.disabled = true;
      els.btnMic.classList.add("unsupported");
      setVoiceStatus(
        "Voice not available in this browser. Use Chrome or Edge, or type."
      );
      return;
    }

    voiceSupported = true;
    els.btnMic.disabled = false;
    els.btnMic.classList.remove("unsupported");

    if (!isSecureEnough()) {
      setVoiceStatus(
        "For voice, open this PC at http://127.0.0.1:5000 in Chrome. On tablet, type works best."
      );
    } else {
      setVoiceStatus("Tap 🎤 Say it, then speak the word.");
    }

    // Use click only — keeps user gesture for recognition.start()
    els.btnMic.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (busy) return;
      startListeningFromGesture();
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
        return;
      }
      // Allow Space in Impossible phrase mode (do not block default)
      if (speakFocus && (e.key === " " || e.code === "Space")) {
        // Let the browser insert the space; input handler will clean it
        return;
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

  if (els.btnHint) {
    els.btnHint.addEventListener("click", function () {
      useHint();
    });
  }

  document.addEventListener("keydown", function (e) {
    if (
      busy ||
      (els.donePanel && !els.donePanel.classList.contains("hidden"))
    )
      return;
    // When typing in the box, browser handles letters + spaces
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
    if (speakFocus && (e.key === " " || e.code === "Space")) {
      e.preventDefault();
      setTyped(typed + " ");
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
