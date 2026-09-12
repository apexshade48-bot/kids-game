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

  function ping(el, cls) {
    if (!el) return;
    el.classList.remove(cls);
    void el.offsetWidth;
    el.classList.add(cls);
  }

  function burst(host) {
    if (!host) return;
    var bits = ["⭐", "✨", "🎉", "💛", "🌟"];
    var i;
    for (i = 0; i < 10; i++) {
      (function (n) {
        var s = document.createElement("span");
        s.className = "fx-star";
        s.textContent = bits[n % bits.length];
        s.style.setProperty("--dx", Math.round(Math.random() * 200 - 100) + "px");
        s.style.setProperty("--dy", Math.round(-24 - Math.random() * 100) + "px");
        s.style.setProperty("--rot", Math.round(Math.random() * 80 - 40) + "deg");
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
    btnHear: document.getElementById("btn-hear"),
    btnHearSlow: document.getElementById("btn-hear-slow"),
    btnHearFast: document.getElementById("btn-hear-fast"),
    btnEcho: document.getElementById("btn-echo"),
    btnExplain: document.getElementById("btn-explain"),
    explainBox: document.getElementById("explain-box"),
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
  const hideWord = root.dataset.hideWord === "1";
  const maxTyped = speakFocus ? 48 : 12;

  function maskWord(word) {
    return String(word || "")
      .split("")
      .map(function (ch) {
        return /[a-z]/i.test(ch) ? "•" : ch;
      })
      .join(" ");
  }

  var speakRate = mode === "letters" || mode === "sounds" || mode === "beginner" ? 0.78 : 0.85;

  function speakText(text, rate) {
    if (!text || !window.speechSynthesis) return false;
    try {
      window.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(String(text));
      u.lang = "en-US";
      u.rate = typeof rate === "number" ? rate : speakRate;
      u.pitch = 1.05;
      window.speechSynthesis.speak(u);
      return true;
    } catch (e) {
      return false;
    }
  }

  function displayWord(word) {
    if (mode === "letters") return String(word || "").toUpperCase();
    return word;
  }

  function showTarget(word, revealed) {
    if (!els.targetWord) return;
    if (hideWord && !revealed) {
      els.targetWord.textContent = maskWord(word);
      els.targetWord.classList.add("is-hidden");
    } else {
      els.targetWord.textContent = displayWord(word);
      els.targetWord.classList.remove("is-hidden");
    }
  }

  function cleanPhraseInput(value) {
    // Allow letters + spaces for Impossible phrases (e.g. "how are you")
    var s = String(value || "").toLowerCase().replace(/[^a-z\s]/g, "");
    // Collapse runs of spaces to a single space, but keep a trailing space while typing
    var trailing = /\s$/.test(s);
    s = s.replace(/\s+/g, " ").replace(/^\s+/, "");
    if (trailing && s.length > 0 && !/\s$/.test(s)) s += " ";
    return s.slice(0, maxTyped);
  }

  function setTyped(value, skipAuto) {
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
      try {
        var len = typed.length;
        els.mobileInput.setSelectionRange(len, len);
      } catch (e) {}
    }
    if (!skipAuto) autoAdvanceIfMatch();
  }

  function exampleWord(item) {
    var speak = String((item && item.speak) || "");
    var m = speak.match(/\sfor\s+([a-z]+)/i);
    return m ? normalize(m[1]) : "";
  }

  function typedIsCorrect(item, answer) {
    var want = normalize(item.word);
    var got = normalize(answer);
    if (!got || !want) return false;
    if (got === want) return true;
    if (mode === "letters") {
      var ex = exampleWord(item);
      if (ex && got === ex) return true;
    }
    return false;
  }

  function autoAdvanceIfMatch() {
    if (busy) return;
    var item = current();
    if (!item) return;
    if (typedIsCorrect(item, typed)) {
      checkAnswer(typed, "type");
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
    showTarget(item.word, false);
    ping(els.wordHint, "word-in");
    ping(els.targetWord, "word-in");
    ping(els.playPanel, "round-in");
    els.progress.textContent = index + 1 + " / " + words.length;
    els.roundScore.textContent = "⭐ " + roundPoints;
    if (els.btnHint) {
      els.btnHint.disabled = false;
      els.btnHint.textContent = "💡 Hint (" + hintCost + "🪙)";
    }
    if (voiceSupported) {
      setVoiceStatus("Tap 🎤 Say it, then speak the word.");
    }
    speakText(item.speak || item.word);
    if (els.explainBox) {
      els.explainBox.textContent = "";
      els.explainBox.classList.add("hidden");
    }
    var teach = document.getElementById("btn-teacher");
    if (teach && item.word) {
      teach.setAttribute("href", "/teacher?word=" + encodeURIComponent(item.word));
    }
    var likeBar = document.getElementById("like-bar");
    if (likeBar) likeBar.classList.add("hidden");
  }

  function askLikeThen(nextFn) {
    var item = current();
    var bar = document.getElementById("like-bar");
    var finished = false;
    function finish() {
      if (finished) return;
      finished = true;
      if (bar) bar.classList.add("hidden");
      nextFn();
    }
    if (!bar || !item) {
      window.setTimeout(finish, 500);
      return;
    }
    bar.classList.remove("hidden");
    ping(bar, "pop-in");
    bar.querySelectorAll("[data-like]").forEach(function (btn) {
      btn.onclick = function () {
        var liked = btn.getAttribute("data-like") === "1";
        fetch("/api/word-like", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            "X-Requested-With": "XMLHttpRequest",
          },
          credentials: "same-origin",
          body: JSON.stringify({ word: item.word, liked: liked }),
        }).catch(function () {});
        if (liked) {
          var stage = document.querySelector(".word-stage");
          burst(stage);
        }
        finish();
      };
    });
    window.setTimeout(finish, 7000);
  }

  function bindKey(btn, insert) {
    var lastTouch = 0;
    function press() {
      if (busy) return;
      if (insert === " ") {
        setTyped(typed + " ");
      } else {
        setTyped(typed + String(insert).toLowerCase());
      }
      els.feedback.textContent = "";
    }
    btn.addEventListener("click", function () {
      if (Date.now() - lastTouch < 600) return;
      press();
    });
    btn.addEventListener("touchend", function (e) {
      e.preventDefault();
      lastTouch = Date.now();
      press();
    });
  }

  function buildKeyboard() {
    const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
    els.keyboard.innerHTML = "";
    letters.forEach(function (letter, i) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "key key-pop";
      btn.style.setProperty("--k", String(i));
      btn.textContent = letter;
      bindKey(btn, letter);
      els.keyboard.appendChild(btn);
    });
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
        body: JSON.stringify({
          mode: mode,
          points: pointsPerWord,
          word: (current() && current().word) || "",
        }),
      });
      const data = await parseJsonResponse(res);
      if (!res.ok) {
        els.feedback.className = "feedback bad";
        els.feedback.textContent =
          (data && data.error) || "Could not save score — try again.";
        return false;
      }
      if (data.daily_bonus) {
        els.feedback.textContent =
          (els.feedback.textContent || "Yes!") + " 🌞 +" + data.daily_bonus + " bonus!";
      }
      if (typeof data.coins === "number") {
        document.querySelectorAll(".top-coins").forEach(function (el) {
          el.textContent = "🪙 " + data.coins;
        });
        var homeCoins = document.getElementById("coin-balance");
        if (homeCoins) homeCoins.textContent = data.coins;
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

  function onCorrect(source) {
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
    var item = current();
    showTarget(item ? item.word : "", true);
    ping(els.targetWord, "celebrate");
    ping(els.wordHint, "celebrate");
    ping(els.roundScore, "score-pop");
    ping(els.feedback, "pop-in");
    var stage = document.querySelector(".word-stage");
    if (stage) {
      stage.classList.add("is-win");
      burst(stage);
      window.setTimeout(function () {
        stage.classList.remove("is-win");
      }, 700);
    }
    try {
      if (sfx && sfx.correct) sfx.correct();
    } catch (e) {}
    awardPoints();

    window.setTimeout(function () {
      if (els.targetWord) els.targetWord.classList.remove("celebrate");
      if (els.roundScore) els.roundScore.classList.remove("score-pop");
      askLikeThen(function () {
        index += 1;
        if (index >= words.length) {
          finishRound();
        } else {
          showWord();
        }
      });
    }, 650);
  }

  function onWrong(heard) {
    els.feedback.className = "feedback bad";
    ping(els.targetWord, "shake");
    ping(els.wordHint, "shake");
    ping(els.playPanel, "shake");
    var miss = current();
    if (window.WordStarsStop) {
      window.WordStarsStop.reportMistake(miss ? miss.word : "", heard || typed || "");
    }
    if (sfx && sfx.wrong) sfx.wrong();
    if (heard) {
      els.feedback.textContent = 'Almost! You said "' + heard + '". Try again!';
    } else {
      els.feedback.textContent = "Not yet — try again!";
    }
  }

  const LETTER_SAY = {
    a: ["a", "ay", "eh", "apple"],
    b: ["b", "be", "bee", "ball"],
    c: ["c", "see", "sea", "cat"],
    d: ["d", "dee", "dog"],
    e: ["e", "ee", "egg"],
    f: ["f", "ef", "fish"],
    g: ["g", "gee", "jee", "gift"],
    h: ["h", "aitch", "hat"],
    i: ["i", "eye", "ice"],
    j: ["j", "jay", "jam"],
    k: ["k", "kay", "key"],
    l: ["l", "el", "ell", "leaf"],
    m: ["m", "em", "moon"],
    n: ["n", "en", "nest"],
    o: ["o", "oh", "owe", "orange"],
    p: ["p", "pee", "pig"],
    q: ["q", "cue", "queue", "queen"],
    r: ["r", "are", "rain"],
    s: ["s", "ess", "sun"],
    t: ["t", "tea", "tee", "tree"],
    u: ["u", "you", "up"],
    v: ["v", "vee", "van"],
    w: ["w", "doubleu", "doubleyou", "web"],
    x: ["x", "ex", "xray"],
    y: ["y", "why", "yam"],
    z: ["z", "zee", "zed", "zebra"],
  };
  const SIGHT_SAY = {
    i: ["i", "eye"],
    you: ["you", "u"],
    the: ["the", "duh", "thee", "da"],
    am: ["am", "im"],
    is: ["is", "iz"],
    my: ["my", "mai"],
    yes: ["yes", "yeah", "yep"],
    no: ["no", "nope"],
  };

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

    // Allow short phrases (up to 3 words) if they contain the target
    if (tokens.length <= 3 && tokens.indexOf(want) !== -1) return true;
    if (tokens.join("") === want) return true;

    var aliases = null;
    if (mode === "letters") aliases = LETTER_SAY[want];
    else if (mode === "beginner") aliases = SIGHT_SAY[want];
    if (aliases) {
      for (var i = 0; i < aliases.length; i++) {
        var al = normalize(aliases[i]);
        if (got === al || (tokens.length <= 3 && tokens.indexOf(al) !== -1)) return true;
      }
      if (tokens[0] === want) return true;
    }

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
    if (
      source === "voice"
        ? speechMatches(answer, want)
        : typedIsCorrect(item, answer)
    ) {
      setTyped(want, true);
      onCorrect(source || "type");
    } else {
      onWrong(source === "voice" ? answer : null);
    }
  }

  function finishRound() {
    hardStopMic();
    els.playPanel.classList.add("hidden");
    els.donePanel.classList.remove("hidden");
    ping(els.donePanel, "win-in");
    burst(els.donePanel);
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

    if (listening || recognition) {
      hardStopMic();
      setVoiceStatus("Stopped. Tap 🎤 Say it to try again.");
      return;
    }

    if (!isSecureEnough()) {
      setVoiceStatus(
        "Voice needs localhost or HTTPS. On this PC use http://127.0.0.1:5000 — or type the word."
      );
    }

    const rec = new SpeechRecognitionCtor();
    recognition = rec;
    lastResultAt = 0;

    rec.lang = "en-US";
    rec.interimResults = true;
    rec.maxAlternatives = 5;
    rec.continuous = false;

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
      if (listening && Date.now() - lastResultAt > 400) {
        setVoiceStatus("Tap 🎤 Say it and try again.");
      }
      setMicListening(false);
      if (recognition === rec) recognition = null;
    };

    try {
      rec.start();
      setMicListening(true);
      setVoiceStatus("Starting mic… speak after the beep / red button.");
    } catch (err) {
      recognition = null;
      setMicListening(false);
      const name = (err && err.name) || "";
      if (name === "InvalidStateError") {
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

    els.btnMic.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (busy) return;
      startListeningFromGesture();
    });
  }

  if (els.mobileInput) {
    var coarse =
      window.matchMedia("(pointer: coarse)").matches ||
      "ontouchstart" in window;
    if (coarse) {
      els.mobileInput.setAttribute("inputmode", "none");
      els.mobileInput.setAttribute("readonly", "readonly");
      els.mobileInput.addEventListener("click", function () {
        els.mobileInput.removeAttribute("readonly");
        els.mobileInput.removeAttribute("inputmode");
        try {
          els.mobileInput.focus({ preventScroll: true });
        } catch (e) {
          els.mobileInput.focus();
        }
      });
    }
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
      if (speakFocus && (e.key === " " || e.code === "Space")) {
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

  function hearNow(rate) {
    var item = current();
    if (!item || busy) return;
    if (!speakText(item.speak || item.word, rate)) {
      setVoiceStatus("Hear it needs a browser that can talk. Try Chrome.");
    }
  }
  if (els.btnHear) {
    els.btnHear.addEventListener("click", function () {
      hearNow(speakRate);
    });
  }
  if (els.btnHearSlow) {
    els.btnHearSlow.addEventListener("click", function () {
      hearNow(0.55);
    });
  }
  if (els.btnHearFast) {
    els.btnHearFast.addEventListener("click", function () {
      hearNow(1.15);
    });
  }
  if (els.btnEcho) {
    els.btnEcho.addEventListener("click", function () {
      if (busy) return;
      setVoiceStatus("Say it with me!");
      hearNow(0.62);
      startListeningFromGesture();
    });
  }
  if (els.btnExplain) {
    els.btnExplain.addEventListener("click", function () {
      var item = current();
      if (!item || busy) return;
      if (!els.explainBox) return;
      els.explainBox.classList.remove("hidden");
      els.explainBox.textContent = "🦉 Thinking…";
      fetch("/api/teacher", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
        body: JSON.stringify({
          word: item.word,
          text: "Explain this word for a small child in two short sentences. Then one easy example.",
        }),
      })
        .then(function (res) {
          return res.json();
        })
        .then(function (data) {
          els.explainBox.textContent =
            "🦉 " + ((data && (data.reply || data.error)) || "Try Teacher in More.");
        })
        .catch(function () {
          els.explainBox.textContent =
            "🦉 Teacher is asleep. Run ollama serve on this PC.";
        });
    });
  }

  document.addEventListener("keydown", function (e) {
    if (
      busy ||
      (els.donePanel && !els.donePanel.classList.contains("hidden"))
    )
      return;
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
