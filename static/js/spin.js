(function () {
  const cfg = window.SPIN_CONFIG || {};
  const wheel = document.getElementById("spin-wheel");
  const btn = document.getElementById("btn-spin");
  const resultEl = document.getElementById("spin-result");
  const coinsEl = document.getElementById("spin-coins");
  const freeBadge = document.getElementById("spin-free-badge");
  const hintEl = document.getElementById("spin-hint");
  const sfx = window.WordStarsSFX || null;

  let freeAvailable = !!cfg.freeAvailable;
  let spinCost = cfg.spinCost || 25;
  let coins = cfg.coins || 0;
  let spinning = false;
  const n = cfg.segmentCount || 8;
  const segAngle = 360 / n;

  // Color segments via conic-gradient
  function paintWheel() {
    if (!wheel) return;
    const colors = [
      "#8b5cf6",
      "#f59e0b",
      "#22c55e",
      "#3b82f6",
      "#94a3b8",
      "#ef4444",
      "#14b8a6",
      "#eab308",
    ];
    const stops = [];
    for (let i = 0; i < n; i++) {
      const a0 = (i / n) * 100;
      const a1 = ((i + 1) / n) * 100;
      stops.push(colors[i % colors.length] + " " + a0 + "% " + a1 + "%");
    }
    wheel.style.background = "conic-gradient(from -90deg, " + stops.join(", ") + ")";
  }

  function updateUi() {
    if (coinsEl) coinsEl.textContent = coins;
    if (freeBadge) {
      freeBadge.textContent = freeAvailable ? "Free spin ready" : "Free used today";
      freeBadge.className =
        "mode-badge " + (freeAvailable ? "mode-badge-free" : "spin-badge-used");
    }
    if (hintEl) {
      hintEl.textContent = freeAvailable
        ? "Your free spin is ready — no coins needed."
        : "Extra spin costs 🪙 " + spinCost + ".";
    }
    if (btn && !spinning) {
      btn.disabled = false;
      btn.textContent = freeAvailable
        ? "Spin free!"
        : "Spin for 🪙 " + spinCost;
      if (!freeAvailable && coins < spinCost) {
        btn.disabled = true;
        btn.textContent = "Need 🪙 " + spinCost;
      }
    }
  }

  function setResult(msg, ok) {
    if (!resultEl) return;
    resultEl.textContent = msg || "";
    resultEl.className = "feedback " + (ok ? "ok" : "bad");
  }

  /**
   * Pointer is at top. Segments are drawn with conic-gradient from -90deg
   * so index 0 starts at top and goes clockwise.
   * Rotate wheel so the middle of segment `index` lands under the pointer.
   */
  function rotationForIndex(index, extraTurns) {
    const turns = extraTurns == null ? 5 : extraTurns;
    const mid = index * segAngle + segAngle / 2;
    // Wheel rotates clockwise in CSS positive deg... actually transform rotate
    // positive is clockwise. We want segment mid at top (0 / -90 in our paint).
    // After rotation R, point that was at angle mid from top goes to top when R = 360 - mid
    // (mod 360), plus full turns.
    return turns * 360 + (360 - mid);
  }

  async function doSpin() {
    if (spinning || !btn || !wheel) return;
    spinning = true;
    btn.disabled = true;
    btn.textContent = "Spinning…";
    setResult("", true);

    const usePaid = !freeAvailable;
    try {
      const res = await fetch("/api/spin", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
        body: JSON.stringify({ paid: usePaid }),
      });
      const text = await res.text();
      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch (e) {
        throw new Error("Could not spin — check server.");
      }
      if (!res.ok) {
        throw new Error(data.error || "Spin failed");
      }

      const idx = typeof data.index === "number" ? data.index : 0;
      const target = rotationForIndex(idx, 6);
      wheel.style.transition = "none";
      // keep current visual rotation base
      const current = getComputedStyle(wheel).transform;
      // reset to 0 then animate for clean multi-turn
      wheel.style.transform = "rotate(0deg)";
      // force reflow
      void wheel.offsetWidth;
      wheel.style.transition = "transform 4.2s cubic-bezier(0.12, 0.75, 0.12, 1)";
      wheel.style.transform = "rotate(" + target + "deg)";

      if (sfx && sfx.click) sfx.click();

      setTimeout(function () {
        coins = data.coins;
        freeAvailable = !!data.free_available;
        if (data.spin_cost) spinCost = data.spin_cost;
        const won = data.amount || 0;
        if (won > 0) {
          setResult(data.message || "You won!", true);
          if (sfx && sfx.correct) sfx.correct();
          if (won >= 100 && sfx && sfx.win) sfx.win();
        } else {
          setResult(data.message || "Try again!", false);
          if (sfx && sfx.wrong) sfx.wrong();
        }
        spinning = false;
        updateUi();
      }, 4300);
    } catch (e) {
      spinning = false;
      setResult(e.message || "Spin failed", false);
      updateUi();
    }
  }

  paintWheel();
  updateUi();
  if (btn) {
    btn.addEventListener("click", doSpin);
  }
})();
