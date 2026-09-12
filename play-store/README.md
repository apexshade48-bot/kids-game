# Publish Word Stars on Google Play

Word Stars is a **website**. Play Store needs an Android wrapper (Trusted Web Activity) that opens your **https://** game.

You cannot skip: a Play Console account (**$25**), a live HTTPS URL, and a signed **.aab**.

## Files in this folder

| File | What you do with it |
|---|---|
| `twa-manifest.json` | Bubblewrap config — set `host` to your live site |
| `build-twa.bat` | Windows: builds the `.aab` after Node + JDK 17 |
| `LISTING.txt` | Copy into Play Console store listing |
| `DATA_SAFETY.txt` | Answers for Data safety |
| `icon-512.png` | App icon (also `../static/icons/icon-512.png`) |
| `feature-graphic.png` | 1024×500 listing banner |

Privacy URL Play will check: `https://YOUR-HOST/privacy`

## 1. Put the game on HTTPS

Laptop `localhost` is not enough. Deploy (Render is easiest — see `DEPLOY_FREE.md`).

Example: `https://word-stars.onrender.com`

Set on the host:

- `SECRET_KEY` = long random string  
- `BEHIND_PROXY=1`  
- `ANDROID_PACKAGE=com.wordstars.app`  
- `ANDROID_CERT_SHA256` = fingerprint after you sign (step 3)

## 2. Play Console

1. [play.google.com/console](https://play.google.com/console) → pay $25 once  
2. **Create app** → name **Word Stars** → **Game** → **Free**  
3. Ads: **No**

**Kids:** this app has player chat. Do **not** tick “Designed for families / kids” unless you turn chat off. Rate **PEGI 3 / Everyone** only if social features are off; otherwise complete the questionnaire honestly (users can message each other). Many family listings get rejected with open chat.

## 3. Build the Android app (TWA)

On this PC install:

- [Node.js LTS](https://nodejs.org/)  
- [JDK 17](https://adoptium.net/)

Edit `twa-manifest.json`: replace `YOUR-HOST` with your site **without** `https://` (example: `word-stars.onrender.com`).

Then:

```bat
cd play-store
build-twa.bat
```

Or:

```bat
npm install -g @bubblewrap/cli
bubblewrap update --manifest twa-manifest.json
bubblewrap build
```

Output: `app-release-bundle.aab`

Get the signing SHA-256 (Bubblewrap prints it, or):

```bat
keytool -list -v -keystore android.keystore
```

Put that fingerprint (with colons, like `AB:CD:...`) in host env `ANDROID_CERT_SHA256`. Open:

`https://YOUR-HOST/.well-known/assetlinks.json`

It must list your package + SHA-256 or the TWA will open in Chrome instead of as an app.

## 4. Store listing (copy from LISTING.txt)

Need at least:

- Title, short + full description  
- Icon 512  
- Feature graphic 1024×500  
- **2 phone screenshots** (capture Home + Spell on a phone; 16:9 or 9:16)  
- Privacy policy URL  

## 5. Upload

Play Console → **Testing → Internal testing** first (add your Gmail). Upload the `.aab`. After it installs on your phone, then Production.

## This repo cannot

- Pay Google  
- Click **Rollout** for you  
- Guarantee approval while **Chat** is open on a “kids 4–5” listing  
