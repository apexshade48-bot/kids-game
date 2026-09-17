(function () {
  var KEY = "wordstars-theme";
  var themes = [
    "violet",
    "ocean",
    "forest",
    "sunset",
    "candy",
    "night",
    "aura",
    "rainbow",
    "beach",
    "snow",
    "meadow",
    "lemon",
    "bubble",
    "lava",
    "galaxy",
    "organic",
  ];

  function apply(theme, opts) {
    opts = opts || {};
    if (!theme || themes.indexOf(theme) === -1) theme = "violet";

    if (theme === "violet") {
      document.documentElement.removeAttribute("data-theme");
    } else {
      document.documentElement.setAttribute("data-theme", theme);
    }

    if (opts.saveLocal !== false) {
      try {
        localStorage.setItem(KEY, theme);
      } catch (e) {}
    }

    var meta = document.querySelector('meta[name="theme-color"]');
    var colors = {
      violet: "#c4b5fd",
      ocean: "#7dd3fc",
      forest: "#86efac",
      sunset: "#fb923c",
      candy: "#f9a8d4",
      night: "#0f172a",
      aura: "#1a0533",
      rainbow: "#fde68a",
      beach: "#38bdf8",
      snow: "#e0f2fe",
      meadow: "#86efac",
      lemon: "#fde047",
      bubble: "#67e8f9",
      lava: "#fb7185",
      galaxy: "#1e1b4b",
      organic: "#f5ead8",
    };
    if (meta) meta.setAttribute("content", colors[theme] || colors.violet);

    document.querySelectorAll(".theme-swatch").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.dataset.theme === theme);
    });

    if (opts.saveServer) {
      fetch("/api/aura", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
        body: JSON.stringify({ aura: theme }),
      }).catch(function () {});
    }
  }

  function current() {
    var body = document.body;
    var account =
      (body && body.getAttribute("data-user-aura")) ||
      document.documentElement.getAttribute("data-theme") ||
      "";
    if (account && themes.indexOf(account) !== -1) return account;
    try {
      return localStorage.getItem(KEY) || "violet";
    } catch (e) {
      return "violet";
    }
  }

  // Prefer account aura from body when available
  document.addEventListener("DOMContentLoaded", function () {
    var account = (document.body && document.body.getAttribute("data-user-aura")) || "";
    if (account && themes.indexOf(account) !== -1) {
      apply(account, { saveLocal: true, saveServer: false });
    } else {
      apply(current(), { saveLocal: false, saveServer: false });
    }

    document.querySelectorAll(".theme-swatch").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var t = btn.dataset.theme || "violet";
        var saveServer = btn.dataset.saveServer === "1";
        apply(t, { saveLocal: true, saveServer: saveServer });
      });
    });
  });

  // Early apply from localStorage (before body)
  try {
    var early = localStorage.getItem(KEY);
    if (early && early !== "violet" && themes.indexOf(early) !== -1) {
      document.documentElement.setAttribute("data-theme", early);
    }
  } catch (e) {}

  window.WordStarsTheme = {
    apply: apply,
    current: current,
    themes: themes,
  };
})();
