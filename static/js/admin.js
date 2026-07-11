(function () {
  const status = document.getElementById("admin-status");

  function showStatus(msg, ok) {
    if (!status) return;
    status.textContent = msg;
    status.className = "admin-status " + (ok ? "ok" : "bad");
    setTimeout(function () {
      status.textContent = "";
      status.className = "admin-status";
    }, 3000);
  }

  async function post(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");
    return data;
  }

  document.querySelectorAll(".btn-save-coins").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.userId;
      const input = document.querySelector(
        '.admin-coins-input[data-user-id="' + userId + '"]'
      );
      try {
        await post("/admin/api/user/" + userId + "/coins", {
          coins: parseInt(input.value, 10),
        });
        showStatus("Coins updated!", true);
      } catch (e) {
        showStatus(e.message, false);
      }
    });
  });

  document.querySelectorAll(".btn-grant-unlock").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.userId;
      const mode = btn.dataset.mode;
      try {
        await post("/admin/api/user/" + userId + "/unlock", { mode: mode });
        showStatus("Unlocked " + mode + "!", true);
        setTimeout(function () {
          window.location.reload();
        }, 600);
      } catch (e) {
        showStatus(e.message, false);
      }
    });
  });

  document.querySelectorAll(".btn-reset-scores").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.userId;
      if (!confirm("Reset all star scores for this player?")) return;
      try {
        await post("/admin/api/user/" + userId + "/reset");
        showStatus("Scores reset!", true);
        setTimeout(function () {
          window.location.reload();
        }, 600);
      } catch (e) {
        showStatus(e.message, false);
      }
    });
  });

  document.querySelectorAll(".btn-promote-admin").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.userId;
      const name = btn.dataset.name;
      if (!confirm("Make \"" + name + "\" an admin? They will get full control of the game.")) return;
      try {
        await post("/admin/api/user/" + userId + "/role", { is_admin: true });
        showStatus(name + " is now an admin!", true);
        setTimeout(function () {
          window.location.reload();
        }, 600);
      } catch (e) {
        showStatus(e.message, false);
      }
    });
  });

  document.querySelectorAll(".btn-demote-admin").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.userId;
      const name = btn.dataset.name;
      if (!confirm("Remove admin access from \"" + name + "\"?")) return;
      try {
        await post("/admin/api/user/" + userId + "/role", { is_admin: false });
        showStatus("Admin access removed from " + name + ".", true);
        setTimeout(function () {
          window.location.reload();
        }, 600);
      } catch (e) {
        showStatus(e.message, false);
      }
    });
  });

  document.querySelectorAll(".btn-delete-user").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.userId;
      const name = btn.dataset.name;
      if (!confirm("Delete player \"" + name + "\"? This cannot be undone.")) return;
      try {
        await post("/admin/api/user/" + userId + "/delete");
        showStatus("Player deleted.", true);
        const row = document.querySelector('tr[data-user-id="' + userId + '"]');
        if (row) row.remove();
      } catch (e) {
        showStatus(e.message, false);
      }
    });
  });
})();