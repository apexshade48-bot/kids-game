/** After a round: Play more, or Stop and email the parent review. */
(function (global) {
  function post(url, body) {
    return fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    }).then(function (res) {
      return res.text().then(function (text) {
        var data = {};
        try {
          data = text ? JSON.parse(text) : {};
        } catch (e) {
          data = { error: "Please log in again." };
        }
        data._status = res.status;
        return data;
      });
    });
  }

  function reportMistake(word, guess) {
    post("/api/play-mistake", { word: word || "", guess: guess || "" }).catch(
      function () {}
    );
  }

  function stopPlaying(btn) {
    if (btn) btn.disabled = true;
    post("/api/play-stop", {})
      .then(function (data) {
        if (data.need_email && data.redirect) {
          window.location.href = data.redirect;
          return;
        }
        if (data.message) {
          try {
            window.alert(data.message);
          } catch (e) {}
        }
        window.location.href = data.redirect || "/home";
      })
      .catch(function () {
        if (btn) btn.disabled = false;
        window.location.href = "/home";
      });
  }

  function bind() {
    document.querySelectorAll("[data-stop-play]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        stopPlaying(btn);
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }

  global.WordStarsStop = { reportMistake: reportMistake, stopPlaying: stopPlaying };
})(window);
