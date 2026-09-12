(function () {
  document.documentElement.classList.add("js-ready");

  var coarse = window.matchMedia("(pointer: coarse)").matches;
  var touch = "ontouchstart" in window || navigator.maxTouchPoints > 0;
  if (coarse || touch) {
    document.documentElement.classList.add("is-touch");
  }

  function setAppHeight() {
    /* innerHeight, not visualViewport — keyboard must not squash the whole app */
    var h = window.innerHeight;
    document.documentElement.style.setProperty("--app-height", h + "px");
  }

  setAppHeight();
  window.addEventListener("resize", setAppHeight);

  window.addEventListener("online", function () {
    document.documentElement.classList.remove("is-offline");
  });
  window.addEventListener("offline", function () {
    document.documentElement.classList.add("is-offline");
  });
  if (!navigator.onLine) {
    document.documentElement.classList.add("is-offline");
  }
})();