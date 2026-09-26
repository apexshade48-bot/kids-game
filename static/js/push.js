(function () {
  var btn = document.getElementById("push-toggle");
  var statusEl = document.getElementById("push-status");
  if (!btn) return;

  function show(msg) {
    if (statusEl) statusEl.textContent = msg || "";
  }

  function urlBase64ToUint8Array(base64String) {
    var padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    var base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    var raw = atob(base64);
    var out = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
    return out;
  }

  function setButtonState(subscribed) {
    btn.textContent = subscribed ? "🔕 Turn off play reminders" : "🔔 Remind me to play";
    btn.dataset.subscribed = subscribed ? "1" : "0";
  }

  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    btn.disabled = true;
    show("Notifications aren't supported on this browser.");
    return;
  }

  async function currentSubscription() {
    var reg = await navigator.serviceWorker.ready;
    return reg.pushManager.getSubscription();
  }

  currentSubscription()
    .then(function (sub) {
      setButtonState(!!sub);
    })
    .catch(function () {
      setButtonState(false);
    });

  btn.addEventListener("click", async function () {
    btn.disabled = true;
    try {
      if (btn.dataset.subscribed === "1") {
        var sub = await currentSubscription();
        if (sub) {
          await fetch("/api/push/unsubscribe", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ endpoint: sub.endpoint }),
          });
          await sub.unsubscribe();
        }
        setButtonState(false);
        show("Reminders turned off.");
        return;
      }

      var keyRes = await fetch("/api/push/public-key");
      var keyData = await keyRes.json();
      if (!keyData.enabled || !keyData.key) {
        show("Reminders aren't set up on this server yet.");
        return;
      }

      var permission = await Notification.requestPermission();
      if (permission !== "granted") {
        show("Notifications were not allowed.");
        return;
      }

      var reg = await navigator.serviceWorker.ready;
      var newSub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(keyData.key),
      });

      var json = newSub.toJSON();
      await fetch("/api/push/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ endpoint: json.endpoint, keys: json.keys }),
      });
      setButtonState(true);
      show("You'll get a nudge if you skip a day!");
    } catch (e) {
      show("Could not update reminders on this device.");
    } finally {
      btn.disabled = false;
    }
  });
})();
