(function () {
  const scene = document.getElementById("space-scene");
  const hint = document.getElementById("space-hint");
  if (!scene) return;

  function sprint(on) {
    scene.classList.toggle("is-sprinting", !!on);
    if (hint) {
      hint.textContent = on ? "Sprinting through space! ✨" : "Tap and hold to sprint 🚀";
    }
  }

  scene.addEventListener("pointerdown", function (e) {
    if (e.target.closest("a, button")) return;
    sprint(true);
  });
  scene.addEventListener("pointerup", function () {
    sprint(false);
  });
  scene.addEventListener("pointercancel", function () {
    sprint(false);
  });
  scene.addEventListener("pointerleave", function () {
    sprint(false);
  });

  document.addEventListener("keydown", function (e) {
    if (e.repeat) return;
    if (e.code === "Space" || e.key === "ArrowUp" || e.key === "w" || e.key === "W") {
      e.preventDefault();
      sprint(true);
    }
  });
  document.addEventListener("keyup", function (e) {
    if (e.code === "Space" || e.key === "ArrowUp" || e.key === "w" || e.key === "W") {
      sprint(false);
    }
  });
})();
