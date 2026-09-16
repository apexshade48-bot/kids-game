# Word Stars — Kids Word Game

A simple browser game for **ages 4–5**. Kids log in, earn coins in Easy mode, unlock higher levels, then **say** or **type** words to earn stars and coins. Works on **phones, tablets, laptops, and desktops**.

Code: [github.com/apexshade48-bot/kids-game](https://github.com/apexshade48-bot/kids-game). Play Store wrap: **PLAY_STORE.md**.

## Features

- **Works on any device** — phone, tablet, laptop (same Wi‑Fi or cloud HTTPS)
- **Login / Sign up** with a name and password  
- **Coin wallet** — earn coins from correct words  
- **Avatar shop** — Roblox-style blocky avatar with **shirts, pants, and accessories**; **Million Shirt** is 1M coins; **Admin / owner shirt, pants, crown** are **1Q coins** (1 quadrillion), only **2 players** can buy them, and they glow with aura  
- **Spell** — **Hear it**, then type or **Say it** (voice). Easy shows the word; Normal+ hides it (picture + sound). **Hint** on hidden words (coins)
- **Quiz** — missing letter · **Pics** — match the emoji to the word  
- **Easy** — free, 8 words, 3 letters (**+20** coins each)  
- **Normal** — unlock for **300 coins**, 8 words, 4 letters (**+35** each)  
- **Hard** — unlock for **5,000 coins**, 10 words, 5–6 letters (**+100** each)  
- **Top** — unlock for **10,000 coins**, 10 words, 7–8 letters (**+500** each)  
- **Family** — unlock for **20,000 coins**, spoken English phrases (**+1,000** each). Hear & say. Admin can unlock free for mom/dad.  
- **Streaks** — coins on day 1 / 3 / 7 (and every 7 days after)  
- **Admin** — coins, unlock/lock modes, reset password, reset stars, roles  
- **Leaderboard** per mode  
- **Sounds** on correct / wrong / round complete

## Run on your computer

```bash
cd kids-word-game
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000** on the computer. Healthcheck: `http://localhost:5000/healthz`.

The terminal prints links for tablets/phones on the same Wi‑Fi, e.g. `http://192.168.1.5:5000`.

## Play on a tablet or phone

1. Keep `python app.py` running on the computer  
2. Connect the tablet/phone to the **same Wi‑Fi**  
3. Open the Wi‑Fi link in **Chrome, Edge, or Safari** (not by copying files)  
4. Log in with the same account  

More help: **http://YOUR-COMPUTER-IP:5000/devices**

### Add to Home Screen (optional)

In the browser menu, choose **Add to Home Screen** for a full-screen app icon.

## Tips

- **Do not copy HTML files** to a tablet — the game needs the Python server running.  
- **Voice** works best in Chrome/Edge on Android and Windows. iPad may need typing.  
- **Typing on tablet:** tap the answer box to open the keyboard, or use A–Z keys.  
- Scores and coins are stored in `kids_word_game.db` on the computer.