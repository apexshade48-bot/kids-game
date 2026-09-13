/** Tiny Web Audio SFX — no external files needed. */
(function (global) {
  var ctx = null;

  function audio() {
    if (!ctx) {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      ctx = new AC();
    }
    if (ctx.state === "suspended") {
      ctx.resume().catch(function () {});
    }
    return ctx;
  }

  function beep(freq, duration, type, gainValue) {
    var c = audio();
    if (!c) return;
    var t0 = c.currentTime;
    var osc = c.createOscillator();
    var g = c.createGain();
    osc.type = type || "sine";
    osc.frequency.value = freq;
    g.gain.setValueAtTime(gainValue || 0.12, t0);
    g.gain.exponentialRampToValueAtTime(0.001, t0 + duration);
    osc.connect(g);
    g.connect(c.destination);
    osc.start(t0);
    osc.stop(t0 + duration);
  }

  global.WordStarsSFX = {
    correct: function () {
      beep(523.25, 0.1, "sine", 0.14);
      setTimeout(function () {
        beep(659.25, 0.12, "sine", 0.14);
      }, 90);
      setTimeout(function () {
        beep(783.99, 0.18, "triangle", 0.12);
      }, 180);
    },
    wrong: function () {
      beep(200, 0.18, "square", 0.08);
      setTimeout(function () {
        beep(150, 0.22, "square", 0.06);
      }, 100);
    },
    win: function () {
      [523, 659, 784, 1047].forEach(function (f, i) {
        setTimeout(function () {
          beep(f, 0.2, "triangle", 0.12);
        }, i * 120);
      });
    },
    click: function () {
      beep(800, 0.04, "sine", 0.05);
    },
    coin: function () {
      beep(880, 0.08, "sine", 0.1);
      setTimeout(function () {
        beep(1174.66, 0.12, "sine", 0.1);
      }, 70);
    },
    unlock: function () {
      [587.33, 739.99, 932.33, 1174.66].forEach(function (f, i) {
        setTimeout(function () {
          beep(f, 0.16, "triangle", 0.11);
        }, i * 90);
      });
    },
  };
})(window);
