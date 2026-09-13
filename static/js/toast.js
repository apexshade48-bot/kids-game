/** Small in-game toast, replaces jarring native alert() popups. */
(function (global) {
  var host = null;

  function getHost() {
    if (host && document.body.contains(host)) return host;
    host = document.createElement("div");
    host.className = "ws-toast-host";
    host.setAttribute("aria-live", "polite");
    document.body.appendChild(host);
    return host;
  }

  function show(message, type, duration) {
    if (!message) return;
    var h = getHost();
    var el = document.createElement("div");
    el.className = "ws-toast" + (type === "bad" ? " ws-toast-bad" : type === "ok" ? " ws-toast-ok" : "");
    el.textContent = message;
    h.appendChild(el);

    var ms = typeof duration === "number" ? duration : 2600;
    window.setTimeout(function () {
      el.classList.add("is-leaving");
      el.addEventListener(
        "animationend",
        function () {
          if (el.parentNode) el.parentNode.removeChild(el);
        },
        { once: true }
      );
    }, ms);

    return el;
  }

  global.WordStarsToast = { show: show };
})(window);
