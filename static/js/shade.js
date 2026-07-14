(function () {
  const status = document.getElementById("shade-status");
  const dumpEl = document.getElementById("shade-dump");
  const listEl = document.getElementById("shade-player-list");

  function show(msg, ok) {
    if (!status) return;
    status.textContent = msg;
    status.className = "admin-status " + (ok ? "ok" : "bad");
    setTimeout(function () {
      status.textContent = "";
      status.className = "admin-status";
    }, 4000);
  }

  async function parseJson(res) {
    const text = await res.text();
    try {
      return text ? JSON.parse(text) : {};
    } catch (e) {
      throw new Error("Server returned non-JSON (log in as Apex?).");
    }
  }

  async function post(action, body) {
    const res = await fetch("/shade/api/" + action, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    });
    const data = await parseJson(res);
    if (!res.ok) throw new Error((data && data.error) || "Failed");
    return data;
  }

  function renderPlayers(users) {
    if (!listEl || !users) return;
    listEl.innerHTML = "";
    users.forEach(function (u) {
      const li = document.createElement("li");
      if (u.is_owner) li.classList.add("is-owner");
      if (u.is_fake) li.classList.add("is-fake");
      if (u.is_banned) li.classList.add("is-banned");
      let badges = "";
      if (u.is_owner) badges += '<span class="admin-badge">APEX</span> ';
      if (u.is_admin && !u.is_owner) badges += '<span class="admin-badge">ADMIN</span> ';
      if (u.is_fake) badges += '<span class="player-badge">FAKE</span> ';
      if (u.is_banned) badges += '<span class="player-badge">BANNED</span> ';
      if (u.god_mode) badges += '<span class="admin-badge">GOD</span> ';
      const s = u.scores || {};
      li.innerHTML =
        "<strong>" +
        (u.name || "?") +
        "</strong> " +
        badges +
        "· 🪙 " +
        (u.coins || 0) +
        " · 🟢" +
        (s.easy || 0) +
        " 🟡" +
        (s.normal || 0) +
        " 🔴" +
        (s.hard || 0) +
        " 💎" +
        (s.top || 0);
      listEl.appendChild(li);
    });
  }

  document.querySelectorAll("[data-action]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const action = btn.dataset.action;
      if (!action) return;

      if (btn.dataset.confirm) {
        if (btn.dataset.needOk) {
          const typed = window.prompt(btn.dataset.confirm + "\nType OK to continue:");
          if (typed !== "OK") {
            show("Cancelled.", false);
            return;
          }
        } else if (!window.confirm(btn.dataset.confirm)) {
          return;
        }
      }

      const body = {};
      if (btn.dataset.needName) {
        const name = (document.getElementById("shade-target") || {}).value || "";
        if (!name.trim()) {
          show("Enter a player username.", false);
          return;
        }
        body.name = name.trim();
      }

      try {
        const data = await post(action, body);
        if (action === "dump" && data.dump) {
          dumpEl.classList.remove("hidden");
          dumpEl.textContent = JSON.stringify(data.dump, null, 2);
          show("System dump ready.", true);
          return;
        }
        show(data.message || "Done.", true);
        if (action === "god_on" || action === "god_off" || action === "reset_me") {
          setTimeout(function () {
            window.location.reload();
          }, 600);
        } else if (
          action === "spawn_fakes" ||
          action === "clear_fakes" ||
          action === "purge_players" ||
          action === "delete" ||
          action === "factory_death"
        ) {
          setTimeout(function () {
            window.location.reload();
          }, 700);
        }
      } catch (e) {
        show(e.message || "Failed", false);
      }
    });
  });

  const injectBtn = document.getElementById("shade-inject-btn");
  if (injectBtn) {
    injectBtn.addEventListener("click", async function () {
      const coins = parseInt(document.getElementById("shade-coins").value, 10);
      const points = parseInt(document.getElementById("shade-points").value, 10);
      try {
        const data = await post("inject", { coins: coins, points: points });
        show(data.message || "Injected.", true);
      } catch (e) {
        show(e.message || "Failed", false);
      }
    });
  }

  const refresh = document.getElementById("shade-refresh");
  if (refresh) {
    refresh.addEventListener("click", async function () {
      try {
        const data = await post("players", {});
        renderPlayers(data.users);
        show("Players refreshed.", true);
      } catch (e) {
        show(e.message || "Failed", false);
      }
    });
  }
})();
