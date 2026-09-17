# Stripe setup — Dashboard steps (not automatable from code)

The subscription code (Checkout, webhooks, revoke-on-dispute) is all in
`app.py` / `database.py` and works out of the box once `STRIPE_SECRET_KEY`,
`STRIPE_PRICE_ID`, and `STRIPE_WEBHOOK_SECRET` are set (see `.env.example`).

The steps below are **account-level configuration in the Stripe Dashboard**.
They are not exposed through the API, so nothing in this repo can turn them
on for you — the account owner has to do this once, by hand.

## 1. Turn on Radar and set it to block/review high-risk payments

Radar (Stripe's built-in fraud scoring) is on by default for every account,
but its default rules only block the most obvious fraud. To actually stop
high-risk card payments before they're captured:

1. Dashboard → **Radar** → **Rules**.
2. Add a rule: **Block if** `risk_level = 'highest'` (blocks the payment
   outright — the checkout fails, no charge happens).
3. Add a second rule: **Request 3D Secure if** `risk_level != 'normal'`
   (pushes borderline payments through 3DS, which shifts chargeback
   liability to the card issuer if the customer disputes it later).
4. Optional, paid tier: **Radar for Fraud Teams** adds manual review queues
   instead of a hard block — worth it once volume is high enough that a
   human reviewing "high risk but not highest" payments makes sense.

Radar runs before the charge is captured, so a blocked payment never
reaches `/webhooks/stripe` as a success at all — the customer sees a
declined card, and no subscription row is ever created for them.

## 2. Prevent one card from farming multiple free trials

Dashboard → **Settings** → **Billing** → **Subscriptions and emails** →
**Free trials** → enable **"Limit customers to one trial per unique
payment method."**

With this on, if a card already redeemed a trial under any account, Stripe
Checkout skips the trial and charges immediately for a second subscription
attempt on that same card — even under a different email/user account. The
app's side of this is already wired up: `/subscribe/card` collects the card
up front even during the trial (`payment_method_collection="always"`) so
this setting has something to check against.

This only covers the **card-based** trial path. The app's separate
self-serve 7-day trial (no card, `/subscribe/trial`) can't be deduped by
Stripe since no card is ever involved — that path is covered instead by
the disposable-email-domain check at signup (`database.py`,
`is_disposable_email_domain`), which is enforced in code and needs no
Dashboard step.

## 3. Configure the retry/dunning schedule (the "grace period")

Dashboard → **Settings** → **Billing** → **Subscriptions and emails** →
**Manage failed payments**. This sets how many times and over how many
days Stripe retries a failed card charge before giving up and canceling
the subscription. The app's own `SUBSCRIPTION_GRACE_DAYS` (5 days, in
`database.py`) is a local safety-net window that keeps access on after the
first `invoice.payment_failed`, but the actual cutoff comes from Stripe
moving the subscription to `canceled`/`unpaid` once its own retries are
exhausted — pick a schedule here you're comfortable with (Stripe's default
is a reasonable few-day retry window).

## 4. Register the webhook endpoint

Dashboard → **Developers** → **Webhooks** → **Add endpoint**:
`https://yourdomain/webhooks/stripe`, and subscribe it to at least:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `invoice.payment_failed`
- `invoice.payment_succeeded`
- `charge.refunded`
- `charge.dispute.created`

Copy the signing secret it gives you into `STRIPE_WEBHOOK_SECRET`.

## None of this is optional for real money

Without step 1, a stolen-card payment sails straight through. Without
step 2, one card can bankroll unlimited free trials under fake accounts.
Without step 4, chargebacks/refunds never reach the app and a disputed
account keeps its access forever. The code enforces the app's half of the
deal; these four Dashboard steps are the account owner's half.
