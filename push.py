"""
Web Push notifications — "come back and play" reminders for kids who have
gone quiet, sent to whatever device installed the app as a PWA.

Why this exists
----------------
The game already rewards a kid who shows up every day (login streaks, the
daily word bonus, the lucky spin). None of that helps if the kid simply
forgets the app exists. A push notification is the only way to reach a
device that isn't currently looking at the app — no email, no SMS, just the
browser's own notification tray, and it costs nothing per message.

This is opt-in and silent by default: nothing is sent unless VAPID keys are
configured (see tools/generate_vapid_keys.py) AND a device has actively
subscribed (browser permission prompt, granted). No subscription, no push —
there is no way to notify a device that never asked to be notified.
"""

from __future__ import annotations

import base64
import os

ENV_PRIVATE_KEY = "VAPID_PRIVATE_KEY_PEM"
ENV_PUBLIC_KEY = "VAPID_PUBLIC_KEY"
ENV_CLAIM_EMAIL = "VAPID_CLAIM_EMAIL"

# How long a kid can go quiet before a reminder is worth sending. Shorter than
# this and a normal "didn't play yesterday" gets nagged; longer and the streak
# the notification would mention is already long gone.
INACTIVE_DAYS_BEFORE_REMINDER = 2


def vapid_config() -> dict:
    """VAPID credentials, or empty strings when not configured.

    The private key is stored in .env with literal '\\n' in place of real
    newlines (a PEM won't fit on one env-var line otherwise) and is unescaped
    here before use.
    """
    private_pem = os.environ.get(ENV_PRIVATE_KEY, "").strip()
    return {
        "private_pem": private_pem.replace("\\n", "\n") if private_pem else "",
        "public_key": os.environ.get(ENV_PUBLIC_KEY, "").strip(),
        "claim_email": os.environ.get(ENV_CLAIM_EMAIL, "").strip(),
    }


def push_enabled() -> bool:
    cfg = vapid_config()
    return bool(cfg["private_pem"] and cfg["public_key"] and cfg["claim_email"])


def vapid_public_key() -> str:
    """The applicationServerKey the browser needs for PushManager.subscribe()."""
    return vapid_config()["public_key"]


class PushSendResult:
    """Outcome of one send attempt, so the caller knows whether to keep,
    retry, or delete the subscription it tried."""

    def __init__(self, ok: bool, gone: bool = False, error: str = ""):
        self.ok = ok
        # 404/410 from the push service means the browser unsubscribed (app
        # uninstalled, browser data cleared, etc) — the subscription is dead
        # and must be deleted, not retried.
        self.gone = gone
        self.error = error


def send_notification(
    subscription_info: dict, title: str, body: str, url: str = "/"
) -> PushSendResult:
    """
    Send one Web Push message. Returns a PushSendResult — never raises for an
    expected failure (unconfigured, expired subscription, network error), so
    a reminder run can loop over many players without one bad subscription
    stopping the rest.
    """
    cfg = vapid_config()
    if not push_enabled():
        return PushSendResult(False, error="Push notifications are not configured.")

    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        return PushSendResult(False, error="pywebpush is not installed.")

    import json

    payload = json.dumps({"title": title, "body": body, "url": url})
    try:
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=cfg["private_pem"],
            vapid_claims={"sub": f"mailto:{cfg['claim_email']}"},
            ttl=60 * 60 * 24,  # a reminder a day late is still useful; a week late is not
        )
        return PushSendResult(True)
    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None) if exc.response else None
        if status in (404, 410):
            return PushSendResult(False, gone=True, error=str(exc))
        return PushSendResult(False, error=str(exc))
    except Exception as exc:  # network/TLS/etc — never let one bad send crash a batch job
        return PushSendResult(False, error=str(exc))


def send_reminders_batch(targets: list[dict]) -> dict:
    """
    Send a reminder to each subscribed-but-quiet player and clean up dead
    subscriptions along the way. `targets` is whatever
    database.list_inactive_players_with_push() returns. Shared by the daily
    scheduled script and the admin panel's manual "send now" button so the
    two never drift apart.
    """
    import database as db

    sent = gone = failed = 0
    for t in targets:
        subscription_info = {
            "endpoint": t["endpoint"],
            "keys": {"p256dh": t["p256dh"], "auth": t["auth"]},
        }
        result = send_notification(
            subscription_info,
            title="Word Stars misses you! ⭐",
            body=f"Come back and keep your streak going, {t['name']}!",
            url="/home",
        )
        if result.ok:
            sent += 1
        elif result.gone:
            db.remove_push_subscription(t["endpoint"])
            gone += 1
        else:
            failed += 1
    return {"sent": sent, "removed_stale": gone, "failed": failed}


def decode_public_key_length(b64url: str) -> int:
    """Sanity-check helper: a valid uncompressed P-256 key decodes to 65 bytes."""
    pad = "=" * (-len(b64url) % 4)
    return len(base64.urlsafe_b64decode(b64url + pad))
