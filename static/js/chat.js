(function () {
  const log = document.getElementById("chat-log");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const statusEl = document.getElementById("chat-status");
  if (!log || !form || !input) return;

  const cfg = window.CHAT_CONFIG || {};
  const withId = cfg.withId || null;
  let lastId = 0;
  let busy = false;

  function showStatus(msg, ok) {
    if (!statusEl) return;
    statusEl.textContent = msg || "";
    statusEl.className = "feedback " + (ok ? "ok" : "bad");
  }

  function esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function nameHtml(msg) {
    const st = esc(msg.name_style || "plain");
    const href = "/player/" + encodeURIComponent(msg.user_id);
    const owner = msg.is_owner
      ? '<span class="pname-owner" title="Owner">⚡</span>'
      : "";
    let inner = esc(msg.name);
    if (st === "wave" || st === "sparkle") {
      inner = String(msg.name || "")
        .split("")
        .map(function (ch, i) {
          return '<span style="--i:' + i + '">' + esc(ch || " ") + "</span>";
        })
        .join("");
    }
    return (
      '<a href="' +
      href +
      '" class="pname pname-' +
      st +
      '" title="Open Apex ID">' +
      inner +
      "</a>" +
      owner
    );
  }

  function addMsg(msg) {
    if (!msg || !msg.id || document.getElementById("chat-m-" + msg.id)) return;
    const row = document.createElement("div");
    row.className = "chat-msg" + (msg.mine ? " is-mine" : "");
    row.id = "chat-m-" + msg.id;
    row.innerHTML =
      '<div class="chat-msg-head">' +
      nameHtml(msg) +
      "</div>" +
      '<p class="chat-msg-body">' +
      esc(msg.body) +
      "</p>";
    log.appendChild(row);
    lastId = Math.max(lastId, msg.id);
    log.scrollTop = log.scrollHeight;
  }

  async function parseJson(res) {
    const text = await res.text();
    try {
      return text ? JSON.parse(text) : {};
    } catch (e) {
      throw new Error("Please log in again.");
    }
  }

  async function pull() {
    const qs = new URLSearchParams({ after: String(lastId) });
    if (withId) qs.set("with", String(withId));
    try {
      const res = await fetch("/api/chat?" + qs.toString(), {
        headers: { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      });
      const data = await parseJson(res);
      if (!res.ok) throw new Error((data && data.error) || "Could not load chat.");
      (data.messages || []).forEach(addMsg);
    } catch (e) {
      showStatus(e.message || "Chat paused.", false);
    }
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    if (busy) return;
    const body = (input.value || "").trim();
    if (!body) return;
    busy = true;
    try {
      const payload = { body: body };
      if (withId) payload.to = withId;
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
        body: JSON.stringify(payload),
      });
      const data = await parseJson(res);
      if (!res.ok) throw new Error((data && data.error) || "Could not send.");
      input.value = "";
      showStatus("", true);
      if (data.message) addMsg(data.message);
    } catch (err) {
      showStatus(err.message || "Could not send.", false);
    }
    busy = false;
    input.focus();
  });

  pull();
  setInterval(pull, 2500);
})();
