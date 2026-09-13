/**
 * Site-wide "new message" notice — not a full read-receipt system, just a
 * lightweight nudge so a kid chatting with a friend/sibling sees a toast and
 * a dot on the Chat tab even while browsing Shop/Space/etc. The chat page
 * itself already polls its own thread every 2.5s; this just watches from
 * everywhere else and leaves a dot lit until they actually open Chat.
 */
(function () {
  var SEEN_KEY = "ws-chat-seen-dm-id";
  var UNREAD_KEY = "ws-chat-unread-flag";
  var isChatPage = document.body && document.body.classList.contains("page-chat");

  function getSeen() {
    try {
      return parseInt(localStorage.getItem(SEEN_KEY) || "0", 10) || 0;
    } catch (e) {
      return 0;
    }
  }

  function setSeen(id) {
    try {
      localStorage.setItem(SEEN_KEY, String(id));
    } catch (e) {}
  }

  function getUnreadFlag() {
    try {
      return localStorage.getItem(UNREAD_KEY) === "1";
    } catch (e) {
      return false;
    }
  }

  function setUnreadFlag(on) {
    try {
      localStorage.setItem(UNREAD_KEY, on ? "1" : "0");
    } catch (e) {}
    markNavUnread(on);
  }

  function markNavUnread(on) {
    var navChat = document.querySelector(
      '.bottom-nav .nav-item[href*="/chat"], .bottom-nav .nav-item[href*="/more"]'
    );
    if (navChat) navChat.classList.toggle("has-unread", !!on);
  }

  // Reflect any already-pending unread immediately, before the first poll.
  markNavUnread(getUnreadFlag());
  if (isChatPage) setUnreadFlag(false);

  async function check() {
    try {
      var res = await fetch("/api/chat/unread", {
        headers: { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      });
      if (!res.ok) return;
      var data = await res.json();
      var maxId = data.max_id || 0;
      var seen = getSeen();

      if (seen === 0) {
        // First check ever on this device — set a baseline, don't notify
        // about the whole pre-existing backlog.
        setSeen(maxId);
        return;
      }

      if (maxId > seen) {
        setSeen(maxId);
        if (isChatPage) {
          setUnreadFlag(false);
        } else {
          setUnreadFlag(true);
          if (window.WordStarsToast) {
            var who = data.from_name ? "from " + data.from_name : "";
            window.WordStarsToast.show("💬 New message " + who, "ok", 3200);
          }
        }
      } else if (isChatPage) {
        setUnreadFlag(false);
      }
    } catch (e) {}
  }

  check();
  setInterval(check, 15000);
})();
