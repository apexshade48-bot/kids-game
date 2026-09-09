(function () {
  const status = document.getElementById("hacker-status");
  const coinsEl = document.getElementById("hacker-coins");

  function show(msg, ok) {
    if (!status) return;
    status.textContent = msg || "";
    status.className = "admin-status " + (ok ? "ok" : "bad");
  }

  async function post(action, body) {
    const res = await fetch("/hacker/api/" + action, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    });
    const text = await res.text();
    var data = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch (e) {
      throw new Error("Log in again.");
    }
    if (!res.ok) throw new Error((data && data.error) || "Hack failed.");
    return data;
  }

  document.querySelectorAll("[data-action]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      var action = btn.dataset.action;
      var body = {};
      if (action === "coins") {
        body.amount = parseInt(btn.dataset.amount, 10) || 0;
      }
      btn.disabled = true;
      try {
        var data = await post(action, body);
        show(data.message || "Done.", true);
        if (coinsEl && typeof data.coins === "number") {
          coinsEl.textContent = data.coins;
        }
      } catch (e) {
        show(e.message || "Failed", false);
      }
      btn.disabled = false;
    });
  });
})();
