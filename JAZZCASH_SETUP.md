# Payment verification

How Word Stars confirms that a parent actually paid, and what each tier can and
cannot protect you against.

The subscription is **1,000 PKR/month** and only ever turns on weekly email
reports. It never unlocks game levels — those are earned with coins by every
child, subscribed or not.

---

## The problem with "send me the transaction ID"

The original flow was:

1. Parent transfers 1,000 PKR to your personal JazzCash number.
2. Parent types the transaction ID from their receipt into a form.
3. An admin opens the JazzCash app, finds the payment, clicks Approve.

**Step 2 is the hole, and it cannot be closed by adding more fields.** A
JazzCash transaction ID is not a secret. It is a short number printed on a
receipt, visible in the app, and readable by anyone standing next to the payer.
A scammer does not have to send any money at all — they only have to read a
stranger's ID and type it in. To the admin, a real-looking ID from a stranger
and a genuine ID from a paying parent are indistinguishable.

So there are two tiers here. Tier 1 makes the manual flow as safe as it can
possibly be. Tier 2 removes the trust problem entirely.

---

## Tier 1 — manual transfer (no merchant account needed)

This works with what you have today. It cannot *prove* a payment, but it removes
every cheap attack and makes the real attack expensive and visible.

### What the parent does

1. Opens `/subscribe` and is shown a **6-character claim code** (e.g. `K7M2QP`).
   It is generated on page load, before any money moves, so there is time to
   copy it. It is stored in their session until they submit.
2. Sends exactly 1,000 PKR to your JazzCash/EasyPaisa number.
3. Pastes the claim code into the transfer's **remarks / note** field.
4. Submits the transaction ID from their receipt, their own sending number,
   and a **screenshot of the receipt** — the screenshot is required; the form
   will not submit without one.

### What you do

In the admin panel, for each pending claim:

1. Open the attached receipt screenshot and your JazzCash app, and find the
   transfer of 1,000 PKR whose **remarks contain the claim code**. This is the
   matching key — it tells you which payment is theirs when three parents paid
   the same amount the same day.
2. Type the **last 4+ characters** of that transfer's transaction ID.
3. Type the **amount that actually arrived** (pre-filled with 1,000).
4. Click Approve — or **Reject as fraud** instead of a plain Reject if you
   believe the claim was never a real payment (an invented ID, or someone
   else's receipt). Two fraud rejections on one account auto-bans it.

### Why the claim code is not authentication

Remarks are chosen by the sender, so anyone can write any code. The code is a
**matching aid**, not proof of payment. Its job is to stop you having to guess
which same-amount transfer belongs to which child.

### The rules the server enforces

These run on every approval. The disabled buttons in the admin panel are a
courtesy only — calling the API directly does not get past them.

| Rule | Why |
|---|---|
| The confirmed ID must appear inside the claimed ID | Stops copy-pasting an unrelated number |
| At least 4 characters of the ID must be echoed back | Forces a real lookup instead of a reflexive click |
| The recorded amount must be ≥ 1,000 PKR | Stops approving a 10 PKR transfer as a subscription |
| A claim expires after **48 hours** | Stops an old genuine receipt being replayed later |
| A transaction ID already claimed by an earlier account blocks the **later** claim only | A real ID clears one payment — but the first claimant keeps access, so a scammer cannot lock out the person who actually paid |
| Max 4 claims per account per day, 12 per IP per day | Stops flooding the admin queue |
| One claim can only be decided once (guarded on `status='pending'`) | Two admins clicking at once cannot grant two months |
| Every decision is written to `subscription_events` with the verified ID and amount | The decision is auditable after the fact |
| A receipt screenshot must be attached before a manual claim can even be created | Typing a number is free; forging a convincing screenshot of a real bank/wallet app is real work, and gives you something to actually look at instead of retyping digits |
| The sending JazzCash/EasyPaisa number is recorded (not verified — no API exists for that) | A forensic/matching aid only; never treated as proof by itself |
| Rejecting a claim as **fraud** (vs. a plain reject) logs a strike; **2 strikes auto-bans the account** | Stops a scammer from re-registering and burning your time one claim at a time; plain "wrong amount / mistyped ID" mistakes never count against an honest parent |

**First claimant wins** is the subtle one. If two accounts quote the same
transaction ID, exactly one of them sent the money. The earlier claim keeps the
benefit of the doubt and the later one is blocked. Blocking both would mean a
scammer could report a stranger's receipt *and* deny that stranger their
subscription.

### What Tier 1 cannot do

- It cannot detect a scammer who invents a transaction ID that **has never been
  used by anyone** and fabricates a matching screenshot (photoshopped, or a
  screenshot of somebody else's real transfer with the amount edited). The
  screenshot requirement raises the cost of this attack — it is no longer
  "type a number you read on a stranger's phone" — but it is not cryptographic
  proof. Only your eyes, cross-checking the screenshot against your own
  JazzCash app, catch a convincing fake.
- It cannot detect a scammer quoting a stranger's ID **if that stranger never
  claimed a subscription here** — there is nothing to compare against.

This is why Tier 2 exists.

---

## Tier 2 — automatic confirmation (needs a JazzCash merchant account)

With this, **no admin ever approves a JazzCash payment**, and there is nothing
left to forge.

### How it works

1. The app mints its own order reference (`pp_TxnRefNo`) — a value the parent
   never sees and never sends back.
2. The parent pays on JazzCash's own hosted page for that reference.
3. JazzCash calls `/webhooks/jazzcash` on success with an HMAC-signed payload.
4. The app verifies the signature, checks the response code and the exact
   amount, and activates the subscription.

The parent supplies **nothing** that the app trusts. The claim is looked up by a
server-generated nonce, so there is no ID to invent, quote from a stranger, or
replay.

If a callback is ever lost (host reboot, proxy timeout, tab closed early), the
parent can press **Check payment** on `/subscribe`, which asks JazzCash directly
via the Transaction Status Inquiry API. Same guarantee: the answer comes from
the gateway, keyed on the reference the parent never had.

### Setup

Get these from your JazzCash integration guide (Jazz Business merchant
services). The URLs are per-merchant and deliberately have **no defaults** —
guessing them fails silently in production.

```bash
JAZZCASH_MERCHANT_ID=...
JAZZCASH_PASSWORD=...              # the API password, NOT your Jazz app login
JAZZCASH_INTEGRITY_SALT=...        # the "Hash Key" / shared secret
JAZZCASH_CHECKOUT_URL=...          # e.g. .../ApplicationAPI/API/2.0/Purchase/SecuredHashPost
JAZZCASH_STATUS_INQUIRY_URL=...    # the Transaction Status Inquiry endpoint
JAZZCASH_RETURN_URL=https://yourdomain/subscribe?paid=1
```

Then register the webhook with JazzCash:

```
POST https://yourdomain/webhooks/jazzcash
```

Subscribed to successful mobile-account/card payments.

`/webhooks/jazzcash` is CSRF-exempt **by design** — the caller is JazzCash's
server, not a browser. Authenticity comes from the signature check, not the
session.

### What Tier 2 stops

| Attack | Tier 1 | Tier 2 |
|---|---|---|
| Invented transaction ID | Only your eyes catch it | **Blocked** — no reference exists |
| Stranger's real transaction ID | Blocked only if that stranger also claimed | **Blocked** — lookup key was never exposed |
| Underpayment (10 PKR) | Blocked if you type the real amount | **Blocked** — amount must match exactly |
| Edited or replayed callback | n/a | **Blocked** — HMAC fails |
| Old receipt replayed | Blocked after 48h | **Blocked** — one claim, one activation |

---

## The signature

JazzCash signs with HMAC-SHA256:

```
message = integritySalt + "&" + value1 + "&" + value2 + ...
hash    = hex( HMAC_SHA256( key = integritySalt, message = message ) )
```

- every `pp_*` field participates, ordered **by field name**
- empty values are skipped entirely (not sent as empty segments)
- `pp_SecureHash` itself never participates
- amounts carry no decimal point: 1,000 PKR is the string `"100000"`

Implemented in `payments.secure_hash()` and checked against the test vector
published in JazzCash's own documentation:

```bash
python tools/verify_jazzcash_hash.py
```

---

## Tests

```bash
python tools/test_payment_security.py    # 53 adversarial checks
python tools/test_payment_regression.py  # existing flows still work
```

`test_payment_security.py` is written as an attack suite: forged callbacks,
edited amounts, replayed receipts, stranger's transaction IDs, rubber-stamped
approvals, and claim flooding. Every one of them must fail to grant access.

---

## Other methods

- **Stripe (card)** — already fully server-authoritative. Webhooks activate,
  Radar handles fraud, and chargeback/dispute/refund webhooks revoke access
  immediately. See `STRIPE_SETUP.md`.
- **EasyPaisa** — Tier 1 only. It has no public merchant verification API, so
  the claim code + amount confirmation is the strongest available control.
- **Free trial** — one per account, 7 days, tracked separately from paid
  subscriptions so the two paths cannot be combined for two free periods.

---

## Anti-abuse limits worth knowing

| Limit | Value | Where |
|---|---|---|
| Claims per account per day | 4 | `CLAIM_LIMIT_PER_ACCOUNT_DAY` |
| Claims per IP per day | 12 | `CLAIM_LIMIT_PER_IP_DAY` |
| Claim validity | 48 hours | `payments.CLAIM_VALID_HOURS` |
| Free trials per account | 1 | `trial_used` column |
| Fraud strikes before auto-ban | 2 | `db.FRAUD_STRIKES_BEFORE_BAN` |

Blocked and mismatched payments are recorded in `subscription_events` and shown
in the admin panel under **Card disputes, refunds & failed payments**. A burst
of `gateway_rejected` entries means either a misconfigured integration or
someone probing for a way in — both worth looking at.
