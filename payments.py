"""
JazzCash merchant integration: request signing, callback verification, and
transaction status inquiry.

Why this module exists
----------------------
The old flow was "parent transfers money to a personal JazzCash number, then
types the transaction ID into a form, and an admin eyeballs it". That cannot be
made safe, because a JazzCash transaction ID is not a secret. Anyone can read
one off a stranger's screen, so an admin looking at a plausible-looking ID has
no way to tell a real payer from someone quoting a stranger's payment. Extra
form fields do not fix that.

The fix is to stop trusting anything the payer supplies. Instead the *server*
creates the order reference (pp_TxnRefNo), JazzCash signs its callback with an
HMAC keyed on the merchant's Integrity Salt, and we activate a subscription
only when that signature verifies and the amount matches. There is then nothing
left to forge: the payment gateway is the source of truth, and no admin action
is involved.

Scheme notes (JazzCash "Hashing Scheme" + "API References" documentation)
------------------------------------------------------------------------
    message = integritySalt + "&" + v1 + "&" + v2 + ...
    hash    = hex( HMAC_SHA256( key = integritySalt, message = message ) )

  * every pp_* field participates, ordered by field NAME (ASCII)
  * empty values are skipped entirely (not sent as empty segments)
  * pp_SecureHash itself never participates
  * amounts carry no decimal point: Rs. 1000 is the string "100000"

tools/verify_jazzcash_hash.py checks this implementation against the test
vector published in JazzCash's own documentation.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone

# JazzCash's own docs describe a successful transaction as response code 000.
JAZZCASH_SUCCESS_CODE = "000"

# Endpoints are deliberately NOT hardcoded. JazzCash hands each merchant a
# base URL and a set of paths in their integration guide, and the paths differ
# between the sandbox and live environments and between API versions. Guessing
# one and shipping it would fail silently in production, so they must be set
# explicitly from the merchant's own documentation.
ENV_MERCHANT_ID = "JAZZCASH_MERCHANT_ID"
ENV_PASSWORD = "JAZZCASH_PASSWORD"
ENV_INTEGRITY_SALT = "JAZZCASH_INTEGRITY_SALT"
ENV_STATUS_URL = "JAZZCASH_STATUS_INQUIRY_URL"
ENV_CHECKOUT_URL = "JAZZCASH_CHECKOUT_URL"
ENV_RETURN_URL = "JAZZCASH_RETURN_URL"

# How long a parent-reported claim stays approvable. A payment receipt is
# checked against the owner's JazzCash app within a day or two; a week-old
# claim is far more likely to be a replay of somebody else's old transfer.
CLAIM_VALID_HOURS = 48


class JazzCashNotConfigured(RuntimeError):
    """Raised when a gateway call is attempted without merchant credentials."""


# --- configuration ---------------------------------------------------------


def jazzcash_config() -> dict | None:
    """Merchant credentials + endpoints, or None when not fully configured."""
    cfg = {
        "merchant_id": os.environ.get(ENV_MERCHANT_ID, "").strip(),
        "password": os.environ.get(ENV_PASSWORD, "").strip(),
        "integrity_salt": os.environ.get(ENV_INTEGRITY_SALT, "").strip(),
        "status_url": os.environ.get(ENV_STATUS_URL, "").strip(),
        "checkout_url": os.environ.get(ENV_CHECKOUT_URL, "").strip(),
        "return_url": os.environ.get(ENV_RETURN_URL, "").strip(),
    }
    # Signing + callback verification need the salt; the inquiry additionally
    # needs an endpoint. Treat those as the two separate capabilities.
    cfg["can_verify_signatures"] = bool(cfg["integrity_salt"])
    cfg["can_inquire"] = bool(
        cfg["merchant_id"] and cfg["password"] and cfg["integrity_salt"] and cfg["status_url"]
    )
    cfg["can_checkout"] = bool(
        cfg["merchant_id"] and cfg["password"] and cfg["integrity_salt"] and cfg["checkout_url"]
    )
    return cfg


def jazzcash_api_enabled() -> bool:
    """True when payments can be confirmed automatically, with no admin step."""
    cfg = jazzcash_config()
    return bool(cfg and cfg["can_inquire"])


def jazzcash_checkout_enabled() -> bool:
    """True when parents can pay through JazzCash's own hosted page."""
    cfg = jazzcash_config()
    return bool(cfg and cfg["can_checkout"])


def jazzcash_signature_enabled() -> bool:
    """True when inbound callbacks can be cryptographically verified."""
    cfg = jazzcash_config()
    return bool(cfg and cfg["can_verify_signatures"])


# --- signing ---------------------------------------------------------------


def amount_to_paisa(pkr: float | int) -> str:
    """JazzCash amounts are integer minor units with no decimal point."""
    return str(int(round(float(pkr) * 100)))


def paisa_to_amount(paisa: str | int) -> float:
    try:
        return round(int(paisa) / 100, 2)
    except (TypeError, ValueError):
        return 0.0


def secure_hash(fields: dict, integrity_salt: str) -> str:
    """
    JazzCash pp_SecureHash.

    Concatenates every non-empty pp_* field value in alphabetical order of the
    field name with '&', prepends the Integrity Salt, and HMAC-SHA256s the
    result using that same salt as the key.
    """
    if not integrity_salt:
        raise JazzCashNotConfigured(
            f"{ENV_INTEGRITY_SALT} is not set - cannot sign or verify JazzCash data."
        )
    parts: list[str] = []
    for name in sorted(fields):
        if not name.lower().startswith("pp_"):
            continue
        if name == "pp_SecureHash":
            continue
        value = fields[name]
        if value is None or value == "":
            continue
        parts.append(str(value))
    message = integrity_salt + "&" + "&".join(parts)
    return hmac.new(
        integrity_salt.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def sign_request(fields: dict) -> dict:
    """Return a copy of `fields` with a correct pp_SecureHash added."""
    cfg = jazzcash_config()
    signed = {k: v for k, v in fields.items() if v is not None and v != ""}
    signed["pp_SecureHash"] = secure_hash(signed, cfg["integrity_salt"])
    return signed


def verify_signature(fields: dict) -> bool:
    """
    Constant-time check of an inbound pp_SecureHash.

    Returns False rather than raising when the salt is missing or the hash is
    absent/malformed: an unverifiable payload is an untrusted payload, and the
    caller must treat it as a failure.
    """
    cfg = jazzcash_config()
    if not cfg["can_verify_signatures"]:
        return False
    given = ""
    for key, value in fields.items():
        if key.lower() == "pp_securehash":
            given = str(value or "")
            break
    if not given:
        return False
    try:
        expected = secure_hash(fields, cfg["integrity_salt"])
    except JazzCashNotConfigured:
        return False
    return hmac.compare_digest(given.strip().lower(), expected.lower())


# --- order references ------------------------------------------------------


def new_txn_ref_no(user_id: int) -> str:
    """
    Server-generated pp_TxnRefNo for a payment attempt.

    This is the whole point of the redesign: the order reference is minted here
    and never shown to, or supplied by, the payer as a claim of payment. A
    payer cannot invent one that resolves to a real payment, and cannot reuse
    someone else's because theirs was never exposed to them.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"WS{int(user_id)}{stamp}{secrets.token_hex(3).upper()}"


def new_claim_code() -> str:
    """
    Short human-typeable code for the manual JazzCash/EasyPaisa flow.

    The parent copies this into the transfer remarks so the owner can match a
    line in their JazzCash app to a specific claim unambiguously. It is a
    matching aid, NOT an authentication factor - remarks are chosen by the
    sender, so anyone can write any code. It exists to stop the owner having to
    guess which of several same-day 1000 PKR transfers belongs to whom.
    """
    # No 0/O/1/I/L: these get read aloud and retyped off a phone screen.
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


def claim_expiry(hours: int = CLAIM_VALID_HOURS) -> str:
    """
    Expiry for a claim, as a UTC **epoch-seconds** string.

    Epoch rather than a formatted date on purpose: SQLite's datetime('now') is
    UTC, so comparing it against a 'YYYY-MM-DD HH:MM:SS' string built from local
    time is off by the machine's UTC offset — on a UTC+5 box a claim meant to
    expire an hour ago still looks valid for another four hours. Epoch seconds
    have no timezone to disagree about.
    """
    import time

    return str(int(time.time()) + int(hours) * 3600)



# --- callback interpretation ----------------------------------------------


def interpret_callback(fields: dict) -> dict:
    """
    Turn a JazzCash callback/IPN payload into a decision-ready dict.

    JazzCash is inconsistent between API versions about whether the success flag
    arrives as pp_ResponseCode ('000'), pp_ResponseMessage, or a status string,
    so every documented spelling is checked. `verified` is deliberately False
    whenever the signature could not be checked - an unsigned callback is never
    treated as proof of payment.
    """
    salt_ok = verify_signature(fields)

    def pick(*names: str) -> str:
        for name in names:
            for key, value in fields.items():
                if key.lower() == name.lower() and value not in (None, ""):
                    return str(value).strip()
        return ""

    response_code = pick("pp_ResponseCode", "pp_responseCode")
    status = pick("pp_Status", "status")
    message = pick("pp_ResponseMessage", "pp_ResponseMsg", "responseMessage")
    amount = pick("pp_Amount", "pp_AmountInPaisa")
    txn_ref = pick("pp_TxnRefNo", "pp_TxnRef")
    tid = pick("pp_TID", "pp_Tid", "tid")
    rrn = pick("pp_RetrievalReferenceNo", "rrn")

    # '000' is the documented success code. A bare success status is also
    # accepted, but only ever alongside a valid signature.
    success = response_code == JAZZCASH_SUCCESS_CODE or status.lower() in (
        "completed",
        "success",
        "successful",
        "captured",
    )
    if not salt_ok:
        success = False

    return {
        "verified": salt_ok,
        "success": success,
        "response_code": response_code,
        "response_message": message,
        "amount_paisa": amount,
        "amount": paisa_to_amount(amount) if amount else None,
        "txn_ref_no": txn_ref,
        "tid": tid,
        "rrn": rrn,
    }


# --- transaction status inquiry -------------------------------------------


def status_inquiry(txn_ref_no: str) -> dict:
    """
    Ask JazzCash whether a payment for this pp_TxnRefNo actually succeeded.

    This is the reconciliation path: if a callback was lost (host reboot, proxy
    timeout, parent closed the tab) the subscription can still be granted, but
    only on JazzCash's own answer, never on the parent's word.

    Raises JazzCashNotConfigured when credentials or the endpoint are missing.
    """
    cfg = jazzcash_config()
    if not cfg["can_inquire"]:
        raise JazzCashNotConfigured(
            "JazzCash status inquiry needs "
            f"{ENV_MERCHANT_ID}, {ENV_PASSWORD}, {ENV_INTEGRITY_SALT} and {ENV_STATUS_URL}."
        )

    payload = sign_request(
        {
            "pp_TxnRefNo": txn_ref_no,
            "pp_MerchantID": cfg["merchant_id"],
            "pp_Password": cfg["password"],
            "pp_Version": "1.1",
        }
    )

    # Imported lazily so the app still runs when the gateway is not in use.
    import json
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        cfg["status_url"],
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        raise JazzCashNotConfigured(
            f"JazzCash status inquiry returned HTTP {exc.code}."
        ) from exc
    except Exception as exc:  # network, TLS, DNS, timeout
        raise JazzCashNotConfigured(
            f"Could not reach JazzCash: {exc}"
        ) from exc

    try:
        data = json.loads(body)
    except ValueError:
        return {
            "ok": False,
            "reason": "unparseable_response",
            "raw": body[:400],
        }
    if not isinstance(data, dict):
        return {"ok": False, "reason": "unexpected_response", "raw": body[:400]}

    status = str(data.get("status") or data.get("pp_Status") or "").strip()
    # Some deployments answer the inquiry with a signed payload; when a hash is
    # present it must verify before the answer is trusted.
    if any(k.lower() == "pp_securehash" for k in data):
        if not verify_signature(data):
            return {"ok": False, "reason": "bad_signature", "raw": body[:400]}

    return {
        "ok": True,
        "status": status,
        # 'Completed'/'Captured' mean money actually moved. Anything else -
        # 'Pending', 'Expired', 'Failed', '' - does not.
        "paid": status.lower() in ("completed", "success", "successful", "captured"),
        "rrn": str(data.get("rrn") or data.get("pp_RetrievalReferenceNo") or ""),
        "settlement_date": str(data.get("settlementDate") or ""),
        "auth_code": str(data.get("authCode") or ""),
    }
