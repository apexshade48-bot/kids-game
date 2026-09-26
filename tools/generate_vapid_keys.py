"""
One-time setup: generate a VAPID key pair for Web Push notifications.

Run:  python tools/generate_vapid_keys.py

Paste the three printed lines into your .env (or PythonAnywhere WSGI file —
see the deploy notes) and set VAPID_CLAIM_EMAIL yourself. Nothing here talks
to a network or any third party; it is pure local key generation.
"""

import base64
import sys

try:
    from py_vapid import Vapid02
except ImportError:
    print("Missing dependency. Run: pip install pywebpush")
    sys.exit(1)

v = Vapid02()
v.generate_keys()

nums = v.public_key.public_numbers()
raw = b"\x04" + nums.x.to_bytes(32, "big") + nums.y.to_bytes(32, "big")
public_b64 = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

private_pem = v.private_pem().decode().strip().replace("\n", "\\n")

print("Add these to your .env:\n")
print(f"VAPID_PRIVATE_KEY_PEM={private_pem}")
print(f"VAPID_PUBLIC_KEY={public_b64}")
print("VAPID_CLAIM_EMAIL=you@example.com   # replace with a real contact address")
