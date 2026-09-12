(function () {
  var log = document.getElementById("teacher-log");
  var form = document.getElementById("teacher-form");
  var input = document.getElementById("teacher-input");
  var send = document.getElementById("teacher-send");
  var status = document.getElementById("teacher-status");
  if (!form || !input || !log) return;

  var history = [];
  var busy = false;
  var word = window.TEACHER_WORD || "";

  function addBubble(text, who) {
    var p = document.createElement("p");
    p.className = "teacher-bubble " + (who === "user" ? "teacher-me" : "teacher-bot");
    p.textContent = text;
    log.appendChild(p);
    log.scrollTop = log.scrollHeight;
  }

  function ask(text) {
    text = String(text || "").trim();
    if (!text || busy) return;
    busy = true;
    if (send) send.disabled = true;
    if (status) status.textContent = "Thinking…";
    addBubble(text, "user");
    history.push({ role: "user", content: text });
    fetch("/api/teacher", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: JSON.stringify({ text: text, word: word, history: history.slice(-6) }),
    })
      .then(function (res) {
        return res.text().then(function (raw) {
          var data = {};
          try {
            data = raw ? JSON.parse(raw) : {};
          } catch (e) {
            data = { error: "Please try again." };
          }
          data._ok = res.ok;
          return data;
        });
      })
      .then(function (data) {
        var reply = (data && (data.reply || data.error)) || "Try again.";
        addBubble(reply, "bot");
        if (data && data.ok) history.push({ role: "assistant", content: reply });
        if (status) status.textContent = data && data.ok ? "" : reply;
      })
      .catch(function () {
        addBubble("Teacher is asleep. Run ollama serve on this PC.", "bot");
      })
      .then(function () {
        busy = false;
        if (send) send.disabled = false;
        input.focus();
      });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var t = input.value;
    input.value = "";
    ask(t);
  });

  document.querySelectorAll("[data-ask]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      ask(btn.getAttribute("data-ask"));
    });
  });

  if (word && input.value) {
    /* leave the prefilled question; kid taps Ask */
  }
})();
