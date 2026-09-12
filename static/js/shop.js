(function () {
  const coinsEl = document.getElementById("shop-coins");
  const statusEl = document.getElementById("shop-status");

  function show(msg, ok) {
    if (!statusEl) return;
    statusEl.textContent = msg || "";
    statusEl.className = "feedback " + (ok ? "ok" : "bad");
  }

  async function parseJson(res) {
    const text = await res.text();
    try {
      return text ? JSON.parse(text) : {};
    } catch (e) {
      throw new Error("Please log in again.");
    }
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
    const data = await parseJson(res);
    if (!res.ok) throw new Error((data && data.error) || "Could not save.");
    return data;
  }

  document.querySelectorAll(".shop-tabs .tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      var slot = tab.dataset.slot;
      document.querySelectorAll(".shop-tabs .tab").forEach(function (t) {
        t.classList.toggle("active", t === tab);
      });
      document.querySelectorAll("[data-slot-panel]").forEach(function (panel) {
        var on = panel.getAttribute("data-slot-panel") === slot;
        panel.classList.toggle("hidden", !on);
        if (on) {
          panel.querySelectorAll(".js-reveal, .shop-card").forEach(function (el) {
            el.classList.add("js-reveal");
            el.classList.add("is-in");
          });
        }
      });
    });
  });

  document.querySelectorAll(".btn-buy").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      if (btn.disabled) return;
      var id = btn.dataset.itemId;
      var cost = parseInt(btn.dataset.cost, 10) || 0;
      btn.disabled = true;
      btn.textContent = "Buying…";
      try {
        var data = await post("/api/shop/buy", { item_id: id });
        if (coinsEl && data.catalog) coinsEl.textContent = data.catalog.coins;
        show(data.message || "Bought!", true);
        setTimeout(function () {
          window.location.reload();
        }, 400);
      } catch (e) {
        show(e.message || "Could not buy.", false);
        btn.disabled = false;
        btn.textContent = cost ? "Buy" : "Get";
      }
    });
  });

  document.querySelectorAll(".btn-equip").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      if (btn.disabled) return;
      btn.disabled = true;
      try {
        var data = await post("/api/shop/equip", { item_id: btn.dataset.itemId });
        show(data.message || "Wearing it!", true);
        setTimeout(function () {
          window.location.reload();
        }, 300);
      } catch (e) {
        show(e.message || "Could not wear.", false);
        btn.disabled = false;
      }
    });
  });

  document.querySelectorAll(".btn-list").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      if (btn.disabled) return;
      var id = btn.dataset.itemId;
      var input = document.querySelector('.sell-price[data-item-id="' + id + '"]');
      var price = input ? parseInt(input.value, 10) : 0;
      btn.disabled = true;
      try {
        var data = await post("/api/shop/list", { item_id: id, price: price });
        show(data.message || "Listed!", true);
        setTimeout(function () {
          window.location.reload();
        }, 350);
      } catch (e) {
        show(e.message || "Could not list.", false);
        btn.disabled = false;
      }
    });
  });

  document.querySelectorAll(".btn-unlist").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      if (btn.disabled) return;
      btn.disabled = true;
      try {
        var data = await post("/api/shop/unlist", {
          listing_id: parseInt(btn.dataset.listingId, 10),
        });
        show(data.message || "Taken down.", true);
        setTimeout(function () {
          window.location.reload();
        }, 350);
      } catch (e) {
        show(e.message || "Could not take down.", false);
        btn.disabled = false;
      }
    });
  });

  document.querySelectorAll(".btn-buy-player").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      if (btn.disabled) return;
      btn.disabled = true;
      btn.textContent = "Buying…";
      try {
        var data = await post("/api/shop/buy-player", {
          listing_id: parseInt(btn.dataset.listingId, 10),
        });
        show(data.message || "Bought! Coins went to the seller.", true);
        setTimeout(function () {
          window.location.reload();
        }, 450);
      } catch (e) {
        show(e.message || "Could not buy.", false);
        btn.disabled = false;
        btn.textContent = "Buy";
      }
    });
  });
})();
