(function () {
  const buttons = document.querySelectorAll(".btn-unlock");
  if (!buttons.length) return;

  const coinBalance = document.getElementById("coin-balance");

  async function parseJsonResponse(res) {
    const text = await res.text();
    try {
      return text ? JSON.parse(text) : {};
    } catch (e) {
      if (res.status === 401 || /<!DOCTYPE|<html/i.test(text)) {
        throw new Error("Session expired — please log in again.");
      }
      throw new Error("Server error. Try again.");
    }
  }

  buttons.forEach(function (btn) {
    btn.addEventListener("click", async function () {
      if (btn.disabled) return;
      const mode = btn.dataset.mode;
      const cost = parseInt(btn.dataset.cost, 10);
      btn.disabled = true;
      btn.textContent = "Unlocking…";

      try {
        const res = await fetch("/api/unlock", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            "X-Requested-With": "XMLHttpRequest",
          },
          credentials: "same-origin",
          body: JSON.stringify({ mode: mode }),
        });
        const data = await parseJsonResponse(res);
        if (!res.ok) {
          alert(data.error || "Could not unlock.");
          btn.disabled = false;
          btn.textContent = "Unlock for 🪙 " + cost;
          return;
        }
        if (
          coinBalance &&
          data.wallet &&
          typeof data.wallet.coins === "number"
        ) {
          coinBalance.textContent = data.wallet.coins;
        }
        window.location.reload();
      } catch (e) {
        var msg = e.message || "Something went wrong — try again!";
        if (/failed to fetch|networkerror|load failed/i.test(msg)) {
          msg =
            "Cannot reach the server. On the PC run: python app.py — then reload this page.";
        }
        alert(msg);
        btn.disabled = false;
        btn.textContent = "Unlock for 🪙 " + cost;
      }
    });
  });
})();
