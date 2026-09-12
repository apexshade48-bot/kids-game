(function () {
  const scene = document.getElementById("space-scene");
  const hint = document.getElementById("space-hint");
  const tilesEl = document.getElementById("space-tiles");
  const sayBox = document.getElementById("space-say");
  const builtEl = document.getElementById("space-built");
  const emojiEl = document.getElementById("space-emoji");
  const input = document.getElementById("space-input");
  const feedback = document.getElementById("space-feedback");
  const progressEl = document.getElementById("space-progress");
  const coinsEl = document.getElementById("space-coins");
  const btnHear = document.getElementById("space-hear");
  const btnMic = document.getElementById("space-mic");
  const btnCheck = document.getElementById("space-check");
  if (!scene || !tilesEl) return;

  const sfx = window.WordStarsSFX || null;
  let word = (scene.dataset.word || "cat").toLowerCase();
  let hintEmoji = scene.dataset.hint || "✨";
  let letters = [];
  try {
    letters = JSON.parse(scene.dataset.letters || "[]");
  } catch (e) {
    letters = word.split("");
  }
  let points = parseInt(scene.dataset.points, 10) || 20;
  const scoreUrl = scene.dataset.scoreUrl || "/api/score";
  const nextUrl = scene.dataset.nextUrl || "/api/space-word";
  let nextIndex = 0;
  let busy = false;
  let collected = [];

  function sprint(on) {
    scene.classList.toggle("is-sprinting", !!on);
  }

  function normalize(s) {
    return String(s || "")
      .toLowerCase()
      .replace(/[^a-z]/g, "");
  }

  function speak(text) {
    if (!text || !window.speechSynthesis) return;
    try {
      window.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(String(text));
      u.lang = "en-US";
      u.rate = 0.85;
      window.speechSynthesis.speak(u);
    } catch (e) {}
  }

  function setFeedback(msg, ok) {
    if (!feedback) return;
    feedback.textContent = msg || "";
    feedback.className = "feedback" + (msg ? (ok ? " ok" : " bad") : "");
  }

  function renderTiles() {
    tilesEl.innerHTML = "";
    nextIndex = 0;
    collected = [];
    if (sayBox) sayBox.classList.add("hidden");
    letters.forEach(function (ch, i) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "space-tile";
      btn.textContent = String(ch).toUpperCase();
      btn.dataset.i = String(i);
      btn.dataset.ch = String(ch).toLowerCase();
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        collect(btn);
      });
      var left = 8 + Math.random() * 72;
      var top = 8 + Math.random() * 58;
      btn.style.left = left + "%";
      btn.style.top = top + "%";
      btn.style.animationDelay = i * 0.12 + "s";
      tilesEl.appendChild(btn);
    });
    if (progressEl) progressEl.textContent = "0 / " + word.length;
    if (hint) {
      hint.textContent = "Tap letters in order to spell the word. Hold to sprint 🚀";
    }
    setFeedback("");
  }

  function collect(btn) {
    if (busy || btn.classList.contains("is-got")) return;
    var want = word[nextIndex];
    var got = btn.dataset.ch;
    if (got !== want) {
      btn.classList.add("is-wrong");
      if (sfx && sfx.wrong) sfx.wrong();
      window.setTimeout(function () {
        btn.classList.remove("is-wrong");
      }, 350);
      if (hint) hint.textContent = "Need " + String(want).toUpperCase() + " next!";
      if (window.WordStarsStop) {
        window.WordStarsStop.reportMistake(word, got);
      }
      return;
    }
    btn.classList.add("is-got");
    collected.push(got);
    nextIndex += 1;
    if (progressEl) progressEl.textContent = nextIndex + " / " + word.length;
    if (sfx && sfx.correct) sfx.correct();
    if (nextIndex >= word.length) {
      openSay();
    }
  }

  function openSay() {
    if (hint) hint.textContent = "You caught them! Hear it, then say or type it.";
    if (emojiEl) emojiEl.textContent = hintEmoji;
    if (builtEl) builtEl.textContent = word.toUpperCase();
    if (input) input.value = "";
    if (sayBox) sayBox.classList.remove("hidden");
    speak(word);
    if (input) {
      try {
        input.focus({ preventScroll: true });
      } catch (e) {}
    }
  }

  function checkSay() {
    if (busy) return;
    var got = normalize(input ? input.value : "");
    if (!got) {
      setFeedback("Type or say the word!", false);
      return;
    }
    if (got !== word) {
      setFeedback("Not yet — try " + word.toUpperCase(), false);
      if (sfx && sfx.wrong) sfx.wrong();
      if (window.WordStarsStop) {
        window.WordStarsStop.reportMistake(word, got);
      }
      return;
    }
    busy = true;
    setFeedback("Yes! +" + points + " 🪙", true);
    if (sfx && sfx.correct) sfx.correct();
    fetch(scoreUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: JSON.stringify({ mode: "easy", points: points, word: word, from: "space" }),
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { res: res, data: data };
        });
      })
      .then(function (pack) {
        if (pack.data && typeof pack.data.coins === "number" && coinsEl) {
          coinsEl.textContent = pack.data.coins;
        }
      })
      .catch(function () {})
      .then(function () {
        window.setTimeout(loadNext, 900);
      });
  }

  function loadNext() {
    fetch(nextUrl, {
      headers: { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin",
    })
      .then(function (res) {
        return res.json();
      })
      .then(function (data) {
        if (!data || !data.word) return;
        word = String(data.word).toLowerCase();
        hintEmoji = data.hint || "✨";
        letters = data.letters || word.split("");
        points = parseInt(data.points, 10) || points;
        busy = false;
        renderTiles();
      })
      .catch(function () {
        busy = false;
        renderTiles();
      });
  }

  var SpeechRecognitionCtor =
    window.SpeechRecognition || window.webkitSpeechRecognition || null;

  function startMic() {
    if (!SpeechRecognitionCtor) {
      setFeedback("Mic not ready — type the word.", false);
      return;
    }
    try {
      var rec = new SpeechRecognitionCtor();
      rec.lang = "en-US";
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      rec.onresult = function (ev) {
        var said = (ev.results[0] && ev.results[0][0] && ev.results[0][0].transcript) || "";
        if (input) input.value = said;
        if (normalize(said) === word || normalize(said).indexOf(word) !== -1) {
          if (input) input.value = word;
          checkSay();
        } else {
          setFeedback('Heard "' + said + '" — try again', false);
        }
      };
      rec.start();
    } catch (e) {
      setFeedback("Could not start mic — type the word.", false);
    }
  }

  scene.addEventListener("pointerdown", function (e) {
    if (e.target.closest("a, button, input")) return;
    sprint(true);
  });
  scene.addEventListener("pointerup", function () {
    sprint(false);
  });
  scene.addEventListener("pointercancel", function () {
    sprint(false);
  });
  scene.addEventListener("pointerleave", function () {
    sprint(false);
  });
  document.addEventListener("keydown", function (e) {
    if (e.repeat) return;
    if (e.target && e.target.id === "space-input") {
      if (e.key === "Enter") {
        e.preventDefault();
        checkSay();
      }
      return;
    }
    if (e.code === "Space" || e.key === "ArrowUp" || e.key === "w" || e.key === "W") {
      e.preventDefault();
      sprint(true);
    }
  });
  document.addEventListener("keyup", function (e) {
    if (e.code === "Space" || e.key === "ArrowUp" || e.key === "w" || e.key === "W") {
      sprint(false);
    }
  });

  if (btnHear) btnHear.addEventListener("click", function () { speak(word); });
  if (btnMic) btnMic.addEventListener("click", startMic);
  if (btnCheck) btnCheck.addEventListener("click", checkSay);

  renderTiles();
})();
