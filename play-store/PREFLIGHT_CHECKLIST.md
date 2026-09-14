# Word Stars — Play Store Pre-Flight Checklist

Publisher: **Future AI** (Pakistan) · Contact: **apexshade16@gmail.com**
Package: `com.wordstars.app` · Live site: `https://apexshade.pythonanywhere.com`

Tick these off in order. Items marked **(you)** can only be done by you (payment, an
account-owner click, or something only you can verify) — I cannot do them for you.

## 1. Android project

- [x] TWA (Trusted Web Activity) using `androidx.browser` + `android-browser-helper`
      — not a raw WebView wrapper (avoids Play's "Minimum Functionality" rejection risk).
- [x] `compileSdk 36` / `targetSdk 36` (Android 16) — required from Aug 31, 2026.
- [x] `minSdk 24` (Android 7+) — runs on the large majority of active devices.
- [x] Gradle 8.11.1 + AGP 8.9.1 (minimum versions that understand API 36).
- [x] `assembleRelease` and `bundleRelease` both build successfully.
- [ ] **(you)** Generate the release keystore and rebuild — see `KEYSTORE.md`.
- [ ] Confirm `versionCode`/`versionName` in `app/build.gradle` before each new upload
      (must increase every time you upload a new build).

## 2. Digital Asset Links (so the app opens with no browser address bar)

- [x] `/.well-known/assetlinks.json` route already exists in `app.py`, driven by the
      `ANDROID_CERT_SHA256` and `ANDROID_PACKAGE` env vars.
- [ ] **(you)** After generating the keystore, get its SHA-256 fingerprint (command
      in `KEYSTORE.md`) and set `ANDROID_CERT_SHA256` on the PythonAnywhere host.
- [ ] **(you)** Reload the PythonAnywhere web app, then check
      `https://apexshade.pythonanywhere.com/.well-known/assetlinks.json` shows your
      fingerprint (not `[]`).
- [ ] Install the signed app on a real phone and confirm it opens full-screen with
      **no browser UI** — that confirms verification worked.

## 3. Store listing (Play Console → Store presence → Main store listing)

- [x] Title: "Word Stars" (10/30 chars).
- [x] Short description (`play-store/LISTING.txt`, under 80 chars).
- [x] Full description (`play-store/LISTING.txt`).
- [x] Release notes for the first release.
- [x] App icon 512×512 (`play-store/icon-512.png`).
- [x] Feature graphic 1024×500 (`play-store/feature-graphic.png`).
- [x] 3 phone screenshots (`play-store/screenshots/`) — **captured from a resized
      browser window, not a real device.** Recommended: replace with real on-device
      screenshots before submitting; Play doesn't require it, but real device
      screenshots look more trustworthy to reviewers and users.
- [ ] Category: Education (confirm "Educational" sub-category in Play Console UI).
- [ ] **(you)** Privacy policy URL: `https://apexshade.pythonanywhere.com/privacy`
      — paste into Play Console → App content → Privacy policy.

## 4. Target audience & content rating (Play Console → App content)

- [ ] **(you)** Target audience questionnaire: answer honestly — this app appeals to
      children among other ages (word/spelling learning). **Do not** enroll in
      "Designed for Families" — player chat is on, and Google routinely rejects
      Families-program apps with open user-to-user chat.
- [ ] **(you)** Content rating questionnaire (IARC): answer "no" to violence, gambling,
      etc. Declare user-generated content / user-to-user communication (chat) — this
      is the main factor that will affect the rating.
- [ ] **(you)** Ads: answer "No" (no ad SDKs in the code).

## 5. Data safety form (Play Console → App content → Data safety)

- [x] Draft answers in `play-store/DATA_SAFETY.txt`, based on reading `app.py` and
      `database.py` — covers name, password (hashed), parent email, game progress,
      chat, and the Web Speech API microphone behavior.
- [ ] **(you)** Copy those answers into the Play Console form.
- [ ] **(you)** Double-check the two "VERIFY BEFORE SUBMITTING" notes at the bottom
      of `DATA_SAFETY.txt` (hosting region; any SDK you add later).

## 6. Permissions

- [x] `RECORD_AUDIO` is declared (used only for the in-browser "Say it" speech
      feature) — Play's Permissions declaration form will ask you to justify this;
      answer: "Used for optional voice-practice/speech-recognition gameplay,
      triggered only when the player taps Say it."
- [x] No other sensitive permissions declared.

## 7. Build & sign

- [ ] **(you)** Run the keystore commands in `KEYSTORE.md`.
- [ ] Rebuild with `./gradlew.bat bundleRelease` (now signed).
- [ ] Verify the signed `.aab` with bundletool (commands in `KEYSTORE.md`).
- [ ] **(you)** In Play Console, opt into **Play App Signing** when prompted on first
      upload — Google then manages the final signing key; you only ever need to keep
      your **upload key** (the one you just generated) safe.

## 8. Testing track

- [ ] **(you)** Play Console → Testing → Internal testing → create a release →
      upload the signed `.aab`.
- [ ] **(you)** Add your own Google account as a tester, install, confirm it opens
      as a real app (no address bar) and the core flows work (login, Letters,
      Shop, Say it).
- [ ] Note: Play's **closed testing** track requires **12 testers opted in for 14
      continuous days** before you can request Production access for a brand-new
      personal developer account (2026 requirement) — plan for this lead time if
      Internal testing alone isn't enough to unlock Production for your account tier.

## 9. Account & payment **(you — cannot be done from here)**

- [ ] Pay Google's one-time $25 Play Console registration fee.
- [ ] Verify developer identity (Play Console now requires ID verification for new
      personal accounts).
- [ ] Click "Create app" → Free → Game → Education.
- [ ] Click **Submit for review** / **Publish** when everything above is green.

## 10. After approval

- [ ] Confirm the live Play listing opens correctly on a real device.
- [ ] Keep the release keystore (`android.keystore` / your `.jks` file) and its
      passwords backed up somewhere safe outside this repo — losing the **upload
      key** before Play App Signing is fully set up means you cannot update the app
      under the same listing.
