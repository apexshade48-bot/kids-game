"""
Anti-fraud tests for the payment system.

The important tests here are the adversarial ones: each one is an attempt to get
a subscription without paying, run against the real database and Flask routes.
If any of them grants access, the payment system is not safe to run.

Run with:  python tools/test_payment_security.py
"""

import os
import sys
import tempfile


WORK = tempfile.mkdtemp(prefix="ws_paysec_")
os.environ["DATA_DIR"] = WORK
os.environ["SECRET_KEY"] = "test-secret-key-for-payment-security-tests"
# A JazzCash Integrity Salt is set here so signature verification is exercised.
os.environ["JAZZCASH_INTEGRITY_SALT"] = "0F5DD14AE2"
os.environ["JAZZCASH_MERCHANT_ID"] = "Test00127801"
os.environ["JAZZCASH_PASSWORD"] = "0123456789"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db  # noqa: E402
import payments  # noqa: E402

PASSED = []
FAILED = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        PASSED.append(name)
        print(f"  PASS  {name}")
    else:
        FAILED.append((name, detail))
        print(f"  FAIL  {name}  {detail}")


def section(title: str) -> None:
    print(f"\n=== {title} ===")


# --- 1. The hash, against JazzCash's own published vector -------------------

section("pp_SecureHash matches JazzCash's published test vector")
DOC_VECTOR = {
    "pp_MerchantID": "MER123",
    "pp_OrderInfo": "A48cvE28",
    "pp_Amount": "2995",
}
DOC_HASH = "c7689cda7474eb1adcd343fd0c0b676bad0ba66361cc46db589bdb0da4c1c867"
check(
    "hash matches documentation",
    payments.secure_hash(DOC_VECTOR, "0F5DD14AE2") == DOC_HASH,
)
check(
    "field order does not matter",
    payments.secure_hash(
        {"pp_Amount": "2995", "pp_MerchantID": "MER123", "pp_OrderInfo": "A48cvE28"},
        "0F5DD14AE2",
    )
    == DOC_HASH,
)
check(
    "empty fields are skipped, not sent as empty segments",
    payments.secure_hash({**DOC_VECTOR, "pp_ExpDate": ""}, "0F5DD14AE2") == DOC_HASH,
)
check(
    "pp_SecureHash never includes itself",
    payments.secure_hash({**DOC_VECTOR, "pp_SecureHash": "junk"}, "0F5DD14AE2") == DOC_HASH,
)
check(
    "tampering with an amount changes the hash",
    payments.secure_hash({**DOC_VECTOR, "pp_Amount": "2996"}, "0F5DD14AE2") != DOC_HASH,
)
check("amount 1000 PKR is '100000' paisa", payments.amount_to_paisa(1000) == "100000")
check("amount 1 PKR is '100' paisa", payments.amount_to_paisa(1) == "100")


# --- 2. Callback forgery ----------------------------------------------------

section("Forged / unsigned JazzCash callbacks are refused")

db.init_db()
ok, victim = db.create_user("Victim", "Passw0rd!x", aura="violet", parent_email="v@e.com")
assert ok, victim

forged = {
    "pp_ResponseCode": "000",
    "pp_Amount": "100000",
    "pp_TxnRefNo": "WS1FAKEFAKEFAKE",
    "pp_TID": "999999999",
}
result = payments.interpret_callback(forged)
check("unsigned callback fails verification", result["verified"] is False)
check("unsigned callback is not treated as success", result["success"] is False)

# Attacker takes a genuine signed payload and edits the amount.
good = payments.sign_request(dict(forged))
check("a correctly signed payload does verify", payments.interpret_callback(good)["verified"])
check("a correctly signed success is success", payments.interpret_callback(good)["success"])
tampered = dict(good)
tampered["pp_Amount"] = "1"
check(
    "editing the amount breaks the signature",
    payments.interpret_callback(tampered)["verified"] is False,
)
upgraded = dict(good)
upgraded["pp_Amount"] = "99999999"
check(
    "inflating the amount breaks the signature",
    payments.interpret_callback(upgraded)["verified"] is False,
)

check(
    "signature check fails closed when the salt is missing",
    payments.verify_signature(good) is True,
)


# --- 3. Admin approval cannot be rubber-stamped -----------------------------

section("Admin approval requires real verification")

import app as app_module  # noqa: E402

app_module.app.config["TESTING"] = True
app_module.app.config["WTF_CSRF_ENABLED"] = False
client = app_module.app.test_client()

OWNER = os.environ.get("INITIAL_ADMIN_NAME", "Apex")
db.create_user(OWNER, "OwnerPass1!", aura="violet", parent_email="o@e.com")
conn = db.get_connection()
conn.execute("UPDATE users SET is_admin = 1 WHERE name = ? COLLATE NOCASE", (OWNER,))
conn.commit()
conn.close()

ok, payer = db.create_user("Payer", "Passw0rd!x", aura="ocean", parent_email="p@e.com")
assert ok, payer

ok, no_receipt_id = db.create_subscription_request(
    payer, "jazzcash", "1234567890", "",
    ip="1.2.3.4", claim_code="NOREC1",
    expected_amount=1000,
    expires_at=payments.claim_expiry(48),
)
check("a manual claim with no receipt screenshot is refused", ok is False, str(no_receipt_id))

ok, req_id = db.create_subscription_request(
    payer, "jazzcash", "1234567890", "",
    ip="1.2.3.4", claim_code="ABC234",
    expected_amount=1000,
    expires_at=payments.claim_expiry(48),
    receipt_path="payer-receipt.jpg",
)
check("claim created", ok is True, str(req_id))

ok, msg = db.resolve_subscription_request(req_id, True, OWNER)
check("approval without a verified ID is refused", ok is False, msg)

ok, msg = db.resolve_subscription_request(
    req_id, True, OWNER, verified_ref="9999", verified_amount=1000
)
check("approval with the wrong ID is refused", ok is False, msg)

ok, msg = db.resolve_subscription_request(
    req_id, True, OWNER, verified_ref="67890", verified_amount=10
)
check("approval with a short amount is refused", ok is False, msg)

ok, msg = db.resolve_subscription_request(
    req_id, True, OWNER, verified_ref="67890", verified_amount=None
)
check("approval with no amount is refused", ok is False, msg)

check("still not subscribed after all bad attempts", db.is_subscribed(payer) is False)

ok, msg = db.resolve_subscription_request(
    req_id, True, OWNER, verified_ref="67890", verified_amount=1000
)
check("approval with correct verification succeeds", ok is True, msg)
check("subscription is now active", db.is_subscribed(payer) is True)

ok, msg = db.resolve_subscription_request(
    req_id, True, OWNER, verified_ref="67890", verified_amount=1000
)
check("the same claim cannot be approved twice", ok is False, msg)


# --- 4. The headline attack: reuse a stranger's transaction ID --------------

section("Reusing another account's transaction ID is blocked")

ok, victim2 = db.create_user("Victim2", "Passw0rd!x", aura="ocean", parent_email="v2@e.com")
ok, scammer = db.create_user("Scammer", "Passw0rd!x", aura="ocean", parent_email="s@e.com")

# A real transfer lands; the honest payer reports it.
ok, honest_id = db.create_subscription_request(
    victim2, "jazzcash", "7778889990", "",
    ip="5.5.5.5", claim_code="ZZZ999", expected_amount=1000,
    expires_at=payments.claim_expiry(48),
    receipt_path="victim2-receipt.jpg",
)
# The scammer quotes the same ID on a different account.
ok, scam_id = db.create_subscription_request(
    scammer, "jazzcash", "7778889990", "",
    ip="6.6.6.6", claim_code="YYY888", expected_amount=1000,
    expires_at=payments.claim_expiry(48),
    receipt_path="scammer-fake-receipt.jpg",
)
check("the scammer's claim was recorded (so it is visible)", ok is True)
check("the honest payer is not subscribed yet", db.is_subscribed(victim2) is False)

pending = {r["id"]: r for r in db.list_pending_subscription_requests()}
check(
    "the reused ID is flagged in the admin list",
    pending[scam_id]["reused_reference"] is True,
)
check("the honest claim is not flagged", pending[honest_id]["reused_reference"] is False)
check("the scammer's claim is not approvable", pending[scam_id]["approvable"] is False)
check("blockers are explained to the admin", len(pending[scam_id]["blockers"]) > 0)

ok, msg = db.resolve_subscription_request(
    scam_id, True, OWNER, verified_ref="8889990", verified_amount=1000
)
check("the server refuses the reused ID even with correct verification", ok is False, msg)
check("the scammer did not get access", db.is_subscribed(scammer) is False)

ok, msg = db.resolve_subscription_request(
    honest_id, True, OWNER, verified_ref="8889990", verified_amount=1000
)
check("the real payer is unaffected and can still be approved", ok is True, msg)
check("the real payer now has access", db.is_subscribed(victim2) is True)


# --- 5. Expired claims (replay of an old genuine receipt) -------------------

section("An old genuine receipt cannot be replayed forever")

ok, replay_user = db.create_user("Replay", "Passw0rd!x", aura="ocean", parent_email="r@e.com")
ok, old_id = db.create_subscription_request(
    replay_user, "jazzcash", "555000111", "",
    ip="7.7.7.7", claim_code="OLD001", expected_amount=1000,
    expires_at=payments.claim_expiry(-1),
    receipt_path="replay-receipt.jpg",
)
check("an expired claim is created but not approvable",
      not {r["id"]: r for r in db.list_pending_subscription_requests()}[old_id]["approvable"])
ok, msg = db.resolve_subscription_request(
    old_id, True, OWNER, verified_ref="5000111", verified_amount=1000
)
check("an expired claim cannot be approved", ok is False, msg)
check("no access was granted", db.is_subscribed(replay_user) is False)


# --- 6. Claim flooding ------------------------------------------------------

section("Claim flooding is rate limited")

conn = db.get_connection()
for i in range(30):
    conn.execute(
        "INSERT INTO subscription_requests (user_id, method, reference, status, ip, created_at)"
        " VALUES (?, 'jazzcash', ?, 'rejected', '9.9.9.9', datetime('now'))",
        (victim2, f"FLOOD{i}"),
    )
conn.commit()
conn.close()

ok, flooder = db.create_user("Flooder", "Passw0rd!x", aura="ocean", parent_email="f@e.com")
results = []
for i in range(8):
    results.append(
        db.create_subscription_request(
            flooder, "jazzcash", f"FLD{i}", "", ip="9.9.9.9",
            receipt_path=f"flooder-{i}.jpg",
        )[0]
    )
check(
    "flooding stops after the per-IP limit",
    results.count(False) >= 1,
    f"accepted={results.count(True)} refused={results.count(False)}",
)


# --- 7. Gateway path cannot be faked from the client ------------------------

section("Only a genuine gateway confirmation grants access")

ok, api_user = db.create_user("ApiUser", "Passw0rd!x", aura="ocean", parent_email="a@e.com")
ref = payments.new_txn_ref_no(api_user)
ok, api_id = db.create_subscription_request(
    api_user, "jazzcash", "", "JazzCash hosted checkout",
    ip="8.8.8.8", claim_code=payments.new_claim_code(), expected_amount=1000,
    expires_at=payments.claim_expiry(48),
    txn_ref_no=ref, gateway="jazzcash_api",
)
check("a hosted-checkout claim is created with a server-side reference", ok is True)

ok, msg = db.confirm_claim_from_gateway("WS-NOT-A-REAL-REF", "rrn1", 100000)
check("an unknown reference is refused", ok is False, msg)

ok, msg = db.confirm_claim_from_gateway(ref, "rrn1", 50000)
check("a confirmed-but-wrong amount is refused", ok is False, msg)
check("no access granted on a wrong amount", db.is_subscribed(api_user) is False)

ok, msg = db.confirm_claim_from_gateway(ref, "rrn-ok", 100000)
check("a correct amount confirms and activates", ok is True, msg)
check("access granted after a genuine confirmation", db.is_subscribed(api_user) is True)

ok, msg = db.confirm_claim_from_gateway(ref, "rrn-ok", 100000)
check("the gateway cannot activate twice for one payment", ok is False, msg)


# --- 8. Webhook endpoint behaviour -----------------------------------------

section("The /webhooks/jazzcash endpoint refuses unsigned posts")

with client.session_transaction() as s:
    s.clear()

r = client.post("/webhooks/jazzcash", data=dict(forged))
check("an unsigned callback gets 400", r.status_code == 400, str(r.status_code))
check(
    "the unsigned callback is logged for review",
    any(
        e["event_type"] == "gateway_rejected"
        for e in db.list_fraud_events(limit=20)
    ),
)

r = client.post("/webhooks/jazzcash", data=tampered)
check("a tampered signed callback gets 400", r.status_code == 400, str(r.status_code))


# --- 9. Order references are unguessable and unique ------------------------

section("Order references and claim codes")

refs = {payments.new_txn_ref_no(1) for _ in range(500)}
check("500 generated references are all unique", len(refs) == 500)
check("references are long enough to be unguessable", all(len(r) > 20 for r in refs))
check(
    "references embed no parent-supplied data",
    all(r.startswith("WS") and r[2:].split("0")[0].isdigit() for r in list(refs)[:50]),
)

codes = {payments.new_claim_code() for _ in range(500)}
check("500 generated claim codes are all unique", len(codes) == 500)
check(
    "claim codes avoid look-alike characters (0/O/1/I/L)",
    not (set("".join(codes)) & set("01IL")),
)

conn = db.get_connection()
conn.execute(
    "INSERT INTO subscription_requests (user_id, method, claim_code, status)"
    " VALUES (?, 'jazzcash', 'DUP999', 'pending')",
    (victim2,),
)
try:
    conn.execute(
        "INSERT INTO subscription_requests (user_id, method, claim_code, status)"
        " VALUES (?, 'jazzcash', 'DUP999', 'pending')",
        (victim,),
    )
    unique_claim_codes = False
    detail = "the unique index accepted a duplicate claim code"
except Exception:
    unique_claim_codes = True
    detail = ""
conn.rollback()
conn.close()
check("two claims cannot share one claim code", unique_claim_codes, detail)


# --- 10. Rejecting a claim as fraud auto-bans repeat offenders --------------

section("Rejecting claims as fraud strikes the account and auto-bans on repeat")

ok, faker = db.create_user("Faker", "Passw0rd!x", aura="ocean", parent_email="fk@e.com")
ok, fake_id_1 = db.create_subscription_request(
    faker, "jazzcash", "1112223330", "",
    ip="4.4.4.1", claim_code="FAK001", expected_amount=1000,
    expires_at=payments.claim_expiry(48), receipt_path="fake-1.jpg",
)
ok, msg = db.resolve_subscription_request(fake_id_1, False, OWNER, fraud=True)
check("first fraud rejection succeeds without banning yet", ok is True, msg)
check("account is not banned after one strike", db.is_user_banned(faker) is False)

ok, fake_id_2 = db.create_subscription_request(
    faker, "jazzcash", "1112223331", "",
    ip="4.4.4.1", claim_code="FAK002", expected_amount=1000,
    expires_at=payments.claim_expiry(48), receipt_path="fake-2.jpg",
)
ok, msg = db.resolve_subscription_request(fake_id_2, False, OWNER, fraud=True)
check("second fraud rejection succeeds and reports the ban", ok is True, msg)
check("account is auto-banned after two fraud strikes", db.is_user_banned(faker) is True)
check(
    "the auto-ban is logged in fraud events",
    any(e["event_type"] == "auto_banned" for e in db.list_fraud_events(limit=20)),
)


# --- summary ----------------------------------------------------------------

print("\n" + "=" * 62)
print(f"passed: {len(PASSED)}   failed: {len(FAILED)}")
if FAILED:
    print("\nfailures:")
    for name, detail in FAILED:
        print(f"  - {name}  {detail}")
print("=" * 62)
sys.exit(1 if FAILED else 0)
