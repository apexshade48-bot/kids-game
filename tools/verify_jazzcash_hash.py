"""
Validate the JazzCash HMAC-SHA256 scheme against the test vector published in
JazzCash's own "Hashing Scheme" documentation.

Published example (sandbox docs, Features -> Hashing Scheme):
    shared secret : 0F5DD14AE2
    pp_MerchantID : MER123
    pp_OrderInfo  : A48cvE28
    pp_Amount     : 2995
    message       : 0F5DD14AE2&2995&MER123&A48cvE28
    expected hash : c7689cda7474eb1adcd343fd0c0b676bad0ba66361cc46db589bdb0da4c1c867
"""
import hashlib
import hmac

SALT = "0F5DD14AE2"
FIELDS = {"pp_MerchantID": "MER123", "pp_OrderInfo": "A48cvE28", "pp_Amount": "2995"}
EXPECTED = "c7689cda7474eb1adcd343fd0c0b676bad0ba66361cc46db589bdb0da4c1c867"


def secure_hash(fields: dict, salt: str) -> str:
    # Only pp_* fields participate, sorted by field name, empty values skipped,
    # pp_SecureHash itself excluded.
    parts = []
    for name in sorted(fields):
        if not name.lower().startswith("pp_"):
            continue
        if name == "pp_SecureHash":
            continue
        value = fields[name]
        if value is None or value == "":
            continue
        parts.append(str(value))
    message = salt + "&" + "&".join(parts)
    return hmac.new(
        salt.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).hexdigest()


got = secure_hash(FIELDS, SALT)
print("message  :", SALT + "&" + "&".join(
    str(FIELDS[k]) for k in sorted(FIELDS)
))
print("computed :", got)
print("expected :", EXPECTED)
print("MATCH    :", hmac.compare_digest(got, EXPECTED))

# The ordering must be by field NAME, not by value — prove that.
shuffled = {"pp_Amount": "2995", "pp_MerchantID": "MER123", "pp_OrderInfo": "A48cvE28"}
print("order-independent (correct):",
      hmac.compare_digest(secure_hash(shuffled, SALT), EXPECTED))

# Empty values must be skipped, not contribute an empty segment.
with_empty = dict(FIELDS)
with_empty["pp_ExpDate"] = ""
print("empty values skipped (correct):",
      hmac.compare_digest(secure_hash(with_empty, SALT), EXPECTED))

# A tampered amount must change the hash.
tampered = dict(FIELDS)
tampered["pp_Amount"] = "2996"
print("tamper detected (correct):",
      not hmac.compare_digest(secure_hash(tampered, SALT), EXPECTED))
