# Word Stars — Google Play Store

**Start here:** folder **`play-store/`** (`README.md`, `LISTING.txt`, `twa-manifest.json`, `build-twa.bat`).

This is a **Flask web game**. Play Store does not host Python apps. The store listing is an Android wrapper (Trusted Web Activity) that opens the **live HTTPS site**.

This is a **Flask web game**. Play Store does not host Python apps. The store listing is an Android wrapper (Trusted Web Activity) that opens the **live HTTPS site**.

You cannot finish a Play Store publish from this PC alone. Google requires:

1. A **Google Play Console** account (one-time **$25** at [play.google.com/console](https://play.google.com/console))
2. A **stable HTTPS URL** (not a laptop tunnel). Render / PythonAnywhere / Fly.
3. A signed **.aab** app bundle
4. Store listing: icon, feature graphic, screenshots, privacy policy, content rating

## Kids / Families policy (important)

The README says ages 4–5. Google’s **Families** program is strict:

- Player **chat** often gets a kids app **rejected** unless it is parent-gated.
- Target **Everyone** / kids only if social features are off or behind a parent PIN.
- Or rate the app **13+** (not a “kids app”) if chat stays open.

Decide that before you submit.

## What is already in this repo

| File | Use |
|---|---|
| `static/icons/icon-512.png` | App icon (512) |
| `static/icons/icon-192.png` | PWA / TWA icon |
| `play-store/feature-graphic.png` | Play listing 1024×500 |
| `/privacy` | Privacy policy page (Play requires a URL) |
| `/.well-known/assetlinks.json` | Digital Asset Links for TWA (fill SHA-256 after you sign) |

Regenerate graphics:

```bash
python tools/generate_play_assets.py
```

## Publish steps

### 1. Put the game on a real HTTPS host

Push this repo, then deploy (Render blueprint `render.yaml`, or PythonAnywhere — see `DEPLOY_FREE.md`).

You need a URL like `https://word-stars.onrender.com` that stays up when this PC is off.

### 2. Create the Play app

1. Open Play Console → **Create app**
2. Name: **Word Stars**
3. Default language: English
4. App or game: **Game**
5. Free
6. Complete the declarations (ads: no)

### 3. Build a Trusted Web Activity (TWA)

On a machine with **JDK 17** and Node:

```bash
npm install -g @bubblewrap/cli
bubblewrap init --manifest https://YOUR-HOST/static/manifest.json
bubblewrap build
```

Package name to use: `com.wordstars.app`

After you have the signing cert SHA-256, set env `ANDROID_CERT_SHA256` on the server (colon-separated Google fingerprint). Then `/ .well-known/assetlinks.json` will match the app.

### 4. Upload

Play Console → **Production** (or Internal testing first) → upload the `.aab` from Bubblewrap.

### 5. Store listing

- Short description: `Hear, say, and spell words. Earn coins and stars.`
- Full description: see README features
- Icon: `static/icons/icon-512.png`
- Feature graphic: `play-store/feature-graphic.png`
- Phone screenshots: Play home, a Spell round, Shop, Leaderboard (need 2+)
- Privacy policy: `https://YOUR-HOST/privacy`
- Category: Educational
- Content rating questionnaire: answer honestly (chat = users can exchange messages)

### 6. What this repo cannot do for you

- Pay the $25 Play fee
- Click **Start rollout to production** on your Console
- Guarantee Google will approve a kids listing while open chat exists

Internal testing (email list) is the fastest way to install on phones before a public listing.
