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

  function friendlyError(e) {
    var msg = (e && e.message) || "Request failed";
    if (/failed to fetch|networkerror|load failed/i.test(msg)) {
      return "Cannot reach the server. Run python app.py on the PC, then reload.";
    }
    return msg;
  }

  async function parseJsonResponse(res) {
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : {};
    } catch (e) {
      if (res.status === 401 || res.redirected || /<!DOCTYPE|<html/i.test(text)) {
        throw new Error("Session expired — please log in again.");
      }
      throw new Error("Server error (not JSON). Status " + res.status);
    }
    return data;
  }

  async function post(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    });
    const data = await parseJsonResponse(res);
    if (!res.ok) throw new Error((data && data.error) || "Request failed");
    return data;
  }

  document.querySelectorAll("[data-resolve-payment]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const requestId = btn.dataset.resolvePayment;
      const approve = btn.dataset.approve === "1";
      const fraud = btn.dataset.fraud === "1";
      const body = { approve: approve, fraud: fraud };

      if (approve) {
        // Deliberate friction: the admin has to state what they actually saw in
        // their JazzCash/EasyPaisa app. The server re-checks both values, so
        // this cannot be bypassed by calling the API directly - it just stops a
        // reflexive click from granting a subscription nobody verified.
        const refInput = document.querySelector('[data-verify-ref="' + requestId + '"]');
        const amtInput = document.querySelector('[data-verify-amount="' + requestId + '"]');
        const ref = refInput ? refInput.value.trim() : "";
        const amount = amtInput ? amtInput.value.trim() : "";
        if (ref.length < 4) {
          showStatus("Type the last 4+ characters of the transaction ID you matched.", false);
          if (refInput) refInput.focus();
          return;
        }
        if (amount === "") {
          showStatus("Record how much PKR actually arrived.", false);
          if (amtInput) amtInput.focus();
          return;
        }
        body.verified_ref = ref;
        body.verified_amount = amount;
        if (
          !confirm(
            "Confirm you found this payment in your own JazzCash/EasyPaisa account:\n\n" +
              "ID ending: " + ref + "\n" +
              "Amount received: " + amount + " PKR\n\n" +
              "Only continue if those match what the parent sent."
          )
        )
          return;
      } else if (fraud) {
        if (
          !confirm(
            "Reject this as a FRAUDULENT claim (invented or stolen transaction ID)?\n\n" +
              "This is logged against the account. After repeated fraudulent claims " +
              "the account is automatically banned. Only use this when you believe " +
              "no real payment was ever made — use plain Reject for honest mistakes " +
              "(wrong amount, mistyped ID, expired claim)."
          )
        )
          return;
      } else if (!confirm("Reject this payment claim?")) {
        return;
      }

      try {
        const res = await post("/admin/api/payments/" + requestId + "/resolve", body);
        showStatus((res && res.message) || (approve ? "Approved - weekly reports on!" : "Rejected."), true);
        const row = document.getElementById("pay-row-" + requestId);
        if (row) row.remove();
      } catch (e) {
        showStatus(friendlyError(e), false);
      }
    });
  });

  const pushBtn = document.getElementById("send-push-reminders");
  if (pushBtn) {
    pushBtn.addEventListener("click", async function () {
      pushBtn.disabled = true;
      try {
        const res = await post("/admin/api/push/send-reminders", {});
        showStatus(
          `Sent ${res.sent}, removed ${res.removed_stale} stale, ${res.failed} failed.`,
          true
        );
      } catch (e) {
        showStatus(friendlyError(e), false);
      } finally {
        pushBtn.disabled = false;
      }
    });
  }

  document.querySelectorAll(".btn-grant-sub").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.userId;
      if (!confirm("Turn on weekly email reports for this player, free for a month? (This does not unlock any levels.)")) return;
      try {
        await post("/admin/api/user/" + userId + "/subscription/grant", {});
        showStatus("Weekly reports turned on!", true);
        setTimeout(function () {
          window.location.reload();
        }, 600);
      } catch (e) {
        showStatus(friendlyError(e), false);
      }
    });
  });

  document.querySelectorAll("[data-revoke-sub]").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.revokeSub;
      if (!confirm("Remove this player's subscription?")) return;
      try {
        await post("/admin/api/user/" + userId + "/subscription/revoke", {});
        showStatus("Subscription removed.", true);
        setTimeout(function () {
          window.location.reload();
        }, 600);
      } catch (e) {
        showStatus(friendlyError(e), false);
      }
    });
  });

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
        showStatus(friendlyError(e), false);
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
        showStatus(friendlyError(e), false);
      }
    });
  });

  document.querySelectorAll(".btn-lock-mode").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.userId;
      const mode = btn.dataset.mode;
      if (!confirm("Lock " + mode + " for this player? They will need to unlock it again."))
        return;
      try {
        await post("/admin/api/user/" + userId + "/lock", { mode: mode });
        showStatus(mode + " locked.", true);
        setTimeout(function () {
          window.location.reload();
        }, 600);
      } catch (e) {
        showStatus(friendlyError(e), false);
      }
    });
  });

  document.querySelectorAll(".btn-lock-all").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.userId;
      const name = btn.dataset.name || "this player";
      if (
        !confirm(
          'Lock Normal, Hard, and Top for "' +
            name +
            '"? Easy stays free.'
        )
      )
        return;
      try {
        await post("/admin/api/user/" + userId + "/lock", { mode: "all" });
        showStatus("Normal, Hard, and Top locked.", true);
        setTimeout(function () {
          window.location.reload();
        }, 600);
      } catch (e) {
        showStatus(friendlyError(e), false);
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
        showStatus(friendlyError(e), false);
      }
    });
  });

  document.querySelectorAll(".btn-reset-password").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.userId;
      const name = btn.dataset.name || "player";
      const password = window.prompt(
        'New password for "' + name + '" (min 3 characters):',
        ""
      );
      if (password === null) return;
      if (!password || password.length < 3) {
        showStatus("Password must be at least 3 characters.", false);
        return;
      }
      if (!confirm('Set password for "' + name + '"?')) return;
      try {
        await post("/admin/api/user/" + userId + "/password", {
          password: password,
        });
        showStatus("Password updated for " + name + ".", true);
      } catch (e) {
        showStatus(friendlyError(e), false);
      }
    });
  });

  document.querySelectorAll(".btn-promote-admin").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.userId;
      const name = btn.dataset.name;
      if (
        !confirm(
          'Make "' + name + '" an admin? They will get full control of the game.'
        )
      )
        return;
      try {
        await post("/admin/api/user/" + userId + "/role", { is_admin: true });
        showStatus(name + " is now an admin!", true);
        setTimeout(function () {
          window.location.reload();
        }, 600);
      } catch (e) {
        showStatus(friendlyError(e), false);
      }
    });
  });

  document.querySelectorAll(".btn-demote-admin").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.userId;
      const name = btn.dataset.name;
      if (!confirm('Remove admin access from "' + name + '"?')) return;
      try {
        await post("/admin/api/user/" + userId + "/role", { is_admin: false });
        showStatus("Admin access removed from " + name + ".", true);
        setTimeout(function () {
          window.location.reload();
        }, 600);
      } catch (e) {
        showStatus(friendlyError(e), false);
      }
    });
  });

  document.querySelectorAll(".btn-delete-user").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const userId = btn.dataset.userId;
      const name = btn.dataset.name;
      if (!confirm('Delete player "' + name + '"? This cannot be undone.'))
        return;
      try {
        await post("/admin/api/user/" + userId + "/delete");
        showStatus("Player deleted.", true);
        const row = document.querySelector('tr[data-user-id="' + userId + '"]');
        if (row) row.remove();
      } catch (e) {
        showStatus(friendlyError(e), false);
      }
    });
  });
})();
