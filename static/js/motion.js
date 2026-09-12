/** Original tab motion: unique enter per screen + scroll reverse. */
(function () {
  var reduced = false;
  try {
    reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) {}

  var lastY = window.scrollY || 0;
  var dir = "down";
  var ticking = false;
  var observer = null;
  var bar = document.querySelector(".scroll-progress-bar");
  var header = document.querySelector(".top-bar");
  var main = document.querySelector(".main-content");

  var REVEAL_SEL = [
    ".hero",
    ".card",
    ".section-card",
    ".mode-card",
    ".board-row",
    ".stat-card",
    ".auth-card",
    ".btn-play-now",
    ".path-chips",
    ".shop-card",
    ".shop-grid",
    ".sell-row",
    ".profile-card",
    ".spin-stage",
    ".chat-card",
    ".shade-hero",
    ".shade-card",
    ".hacker-hero",
    ".hacker-card",
    ".coin-hint",
    ".battle-player-card",
    ".battle-vs",
    ".done-card",
  ].join(",");

  function pageId() {
    var cls = (document.body && document.body.className) || "";
    var m = cls.match(/page-([a-z-]+)/);
    return m ? m[1] : "home";
  }

  function setEnterDirection() {
    var order = {
      home: 0,
      shop: 1,
      space: 2,
      battle: 3,
      "battle-play": 3,
      spin: 4,
      chat: 5,
      leaderboard: 6,
      profile: 6,
      admin: 7,
      hacker: 8,
      shade: 9,
      play: 0,
      quiz: 0,
      login: -1,
    };
    var now = order[pageId()];
    if (typeof now !== "number") now = 0;
    var prev = 0;
    try {
      prev = parseInt(sessionStorage.getItem("ws-tab") || "0", 10) || 0;
      sessionStorage.setItem("ws-tab", String(now));
    } catch (e) {}
    document.documentElement.setAttribute(
      "data-enter",
      now > prev ? "right" : now < prev ? "left" : "up"
    );
    document.documentElement.setAttribute("data-page", pageId());
  }

  function onScroll() {
    var y = window.scrollY || 0;
    if (Math.abs(y - lastY) > 4) {
      var next = y > lastY ? "down" : "up";
      if (next !== dir) {
        dir = next;
        document.documentElement.setAttribute("data-scroll-dir", dir);
      }
    }
    document.documentElement.classList.toggle("is-scrolled", y > 12);
    if (header) header.classList.toggle("is-compact", y > 28);
    var hero = document.querySelector(".hero, .hacker-hero, .shade-hero");
    if (hero && !reduced) {
      hero.style.setProperty("--hero-shift", Math.min(28, y * 0.18) + "px");
    }
    if (bar) {
      var max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      bar.style.transform = "scaleX(" + Math.min(1, y / max) + ")";
    }
    lastY = y;
    ticking = false;
  }

  function requestTick() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(onScroll);
  }

  function isHidden(el) {
    return (
      !el ||
      (el.classList && el.classList.contains("hidden")) ||
      (el.closest && el.closest(".hidden"))
    );
  }

  function markReveals(root) {
    var scope = root || document;
    var i = 0;
    scope.querySelectorAll(REVEAL_SEL).forEach(function (el) {
      if (el.closest(".bottom-nav, .top-bar, .offline-banner, .keyboard, .play-panel, .shop-tabs, .tabs"))
        return;
      el.classList.add("js-reveal");
      el.style.setProperty("--i", String(i % 10));
      if (el.closest(".hidden")) {
        el.classList.add("is-in");
      }
      i += 1;
    });
    if (!root && main) {
      Array.prototype.forEach.call(main.children, function (el) {
        if (el.classList.contains("hidden")) return;
        if (el.id === "play-panel" || el.id === "quiz-panel" || el.id === "game-root")
          return;
        el.classList.add("js-reveal");
      });
    }
  }

  function observeAll() {
    var nodes = document.querySelectorAll(".js-reveal");
    if (reduced) {
      nodes.forEach(function (el) {
        el.classList.add("is-in");
      });
      return;
    }
    if (!("IntersectionObserver" in window)) {
      nodes.forEach(function (el) {
        if (!isHidden(el)) el.classList.add("is-in");
      });
      return;
    }
    if (observer) observer.disconnect();
    var cls = (document.body && document.body.className) || "";
    var reverse = cls.indexOf("page-home") !== -1;
    observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (isHidden(entry.target)) return;
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
          } else if (reverse && !entry.target.classList.contains("shop-card")) {
            entry.target.classList.remove("is-in");
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    nodes.forEach(function (el) {
      observer.observe(el);
    });
  }

  function replay(root) {
    var scope = root || document;
    markReveals(scope);
    var nodes = [];
    if (scope.classList && scope.classList.contains("js-reveal")) nodes.push(scope);
    scope.querySelectorAll(".js-reveal").forEach(function (el) {
      nodes.push(el);
    });
    nodes.forEach(function (el, i) {
      el.classList.remove("is-in");
      el.style.setProperty("--i", String(i % 10));
    });
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        nodes.forEach(function (el) {
          if (!isHidden(el)) el.classList.add("is-in");
        });
      });
    });
  }

  setEnterDirection();
  document.documentElement.setAttribute("data-scroll-dir", "down");
  var isTouch =
    document.documentElement.classList.contains("is-touch") ||
    "ontouchstart" in window ||
    (navigator.maxTouchPoints || 0) > 0;

  if (main) {
    if (isTouch || reduced) {
      main.classList.add("is-ready");
    } else {
      main.classList.add("page-enter");
      window.requestAnimationFrame(function () {
        main.classList.add("is-ready");
      });
    }
  }
  if (reduced || isTouch) {
    document.querySelectorAll(".js-reveal").forEach(function (el) {
      el.classList.add("is-in");
    });
  } else {
    markReveals();
    observeAll();
  }
  window.setTimeout(function () {
    document.querySelectorAll(".js-reveal").forEach(function (el) {
      el.classList.add("is-in");
    });
    if (main) main.classList.add("is-ready");
  }, 1200);
  window.addEventListener("scroll", requestTick, { passive: true });

  window.WordStarsMotion = { replay: replay, mark: markReveals };
})();
