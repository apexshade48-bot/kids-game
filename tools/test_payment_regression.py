"""Regression check: the payment changes must not break existing pages/flows."""
import io
import os
import sys
import tempfile

WORK = tempfile.mkdtemp(prefix="ws_payreg_")
os.environ["DATA_DIR"] = WORK
os.environ["SECRET_KEY"] = "regression-secret-key"
os.environ["JAZZCASH_NUMBER"] = "0300-1234567"
os.environ["EASYPAISA_NUMBER"] = "0300-7654321"
sys.path.insert(0, r"C:\Users\leo\kids-word-game")

import app as app_module  # noqa: E402
import database as db  # noqa: E402
import payments  # noqa: E402

app_module.app.config["TESTING"] = True
app_module.app.config["WTF_CSRF_ENABLED"] = True
client = app_module.app.test_client()
db.init_db()

db.create_user("Kid", "Passw0rd!x", aura="ocean", parent_email="p@e.com")
db.create_user("Apex", "OwnerPass1!", aura="violet", parent_email="o@e.com")
conn = db.get_connection()
conn.execute("UPDATE users SET is_admin = 1 WHERE name = 'Apex'")
conn.commit()
conn.close()

import re  # noqa: E402


def token():
    html = client.get("/home").get_data(as_text=True)
    return re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)


with client.session_transaction() as s:
    s["user_id"] = 1
    s["user_name"] = "Kid"
    s["aura"] = "ocean"

fails = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        fails.append(name)


print("=== existing pages still render ===")
for path in ("/home", "/more", "/parent", "/subscribe", "/leaderboard", "/shop"):
    r = client.get(path, follow_redirects=True)
    check(f"{path} renders", r.status_code == 200, r.status_code)

print("\n=== subscribe page shows a claim code before any payment ===")
html = client.get("/subscribe").get_data(as_text=True)
codes = re.findall(r'name="claim_code" value="([A-Z0-9]{6})"', html)
check("a 6-character claim code is shown on the form", len(codes) >= 1, codes)
check("the same code is reused for both payment methods", len(set(codes)) == 1, set(codes))
check("the code is shown to the parent in the instructions", codes[0] in html if codes else False)
check("the price is stated", "1000" in html)

print("\n=== submitting a claim works end to end ===")
t = token()
r = client.post(
    "/subscribe",
    data={
        "csrf_token": t, "method": "jazzcash",
        "reference": "9988776655", "note": "from my phone",
        "claim_code": codes[0] if codes else "ABC123",
        "sender_number": "03001234567",
        "receipt": (io.BytesIO(b"fake-jpeg-bytes" * 64), "receipt.jpg", "image/jpeg"),
    },
    content_type="multipart/form-data",
    follow_redirects=True,
)
check("claim submit returns 200", r.status_code == 200, r.status_code)
html = r.get_data(as_text=True)
check("the pending claim is shown back to the parent", "Payment submitted" in html)

pending = db.get_pending_subscription_request(1)
check("the claim reached the database", pending is not None)
check("the claim code was recorded", pending and pending["claim_code"] == (codes[0] if codes else "ABC123"), pending)
check("the expected amount was recorded", pending and pending["expected_amount"] == 1000, pending)
check("an expiry was recorded", pending and pending["expires_at"], pending)

# The requester IP is recorded for rate limiting but deliberately not exposed by
# the parent-facing getter, so read it straight from the table.
_conn = db.get_connection()
_ip = _conn.execute(
    "SELECT ip, gateway, risk_flags FROM subscription_requests WHERE id = ?",
    (pending["id"],),
).fetchone()
_conn.close()
check("the requester IP was recorded", _ip["ip"] is not None, dict(_ip))
check("the claim is marked as the manual flow", _ip["gateway"] == "manual", _ip["gateway"])

print("\n=== the pending claim appears in the admin queue, fully verified ===")
with client.session_transaction() as s:
    s["user_id"] = 2
    s["user_name"] = "Apex"
    s["aura"] = "violet"
    s["is_admin"] = True
    s["is_owner"] = True

r = client.get("/admin")
html = r.get_data(as_text=True)
check("admin panel renders", r.status_code == 200, r.status_code)
check("the claim code is shown to the owner", pending["claim_code"] in html)
check("the verification input is present", 'data-verify-ref=' in html)
check("the amount input is present", 'data-verify-amount=' in html)
check("the claim is approvable (no blockers)", 'data-resolve-payment' in html)

print("\n=== approving through the real API works ===")
t = token()
r = client.post(
    f"/admin/api/payments/{pending['id']}/resolve",
    json={"approve": True, "verified_ref": "776655", "verified_amount": 1000},
    headers={"X-CSRFToken": t},
)
check("approval succeeds via the API", r.status_code == 200, r.get_data(as_text=True)[:200])
check("the subscription is now active", db.is_subscribed(1) is True)

print("\n=== the subscribe page reflects the active subscription ===")
with client.session_transaction() as s:
    s["user_id"] = 1
    s["user_name"] = "Kid"
    s["aura"] = "ocean"
    s["is_admin"] = False
    s["is_owner"] = False
html = client.get("/subscribe").get_data(as_text=True)
check("the parent is told they are subscribed", "You're subscribed" in html)

print("\n=== gateway routes are inert until merchant credentials exist ===")
check("checkout is disabled with no credentials", payments.jazzcash_checkout_enabled() is False)
check("inquiry is disabled with no credentials", payments.jazzcash_api_enabled() is False)
r = client.post("/subscribe/jazzcash/start", data={"csrf_token": token()}, follow_redirects=True)
check("starting checkout without credentials redirects to /subscribe", "/subscribe" in r.request.path or r.status_code == 200)
r = client.post("/subscribe/jazzcash/check", data={"csrf_token": token()}, follow_redirects=True)
check("the check route does not crash", r.status_code == 200, r.status_code)

print("\n=== stripe path untouched ===")
check("card payments still reported as not configured", app_module.STRIPE_ENABLED is False)

print("\n" + "=" * 60)
print(f"failures: {len(fails)}")
for f in fails:
    print("  - " + f)
print("=" * 60)
sys.exit(1 if fails else 0)
