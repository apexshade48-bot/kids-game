(function () {
  const buttons = document.querySelectorAll(".btn-unlock");
  if (!buttons.length) return;

  const coinBalance = document.getElementById("coin-balance");

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
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ mode: mode }),
        });
        const data = await res.json();
        if (!res.ok) {
          alert(data.error || "Could not unlock.");
          btn.disabled = false;
          btn.textContent = "Unlock for 🪙 " + cost;
          return;
        }
        window.location.reload();
      } catch (e) {
        alert("Something went wrong — try again!");
        btn.disabled = false;
        btn.textContent = "Unlock for 🪙 " + cost;
      }
    });
  });
})();