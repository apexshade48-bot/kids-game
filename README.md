# Word Stars — Kids Word Game

A simple browser game for **ages 4–5**. Kids log in, earn coins in Easy mode, unlock higher levels, then **say** or **type** words to earn stars and coins. Works on **phones, tablets, laptops, and desktops**.

## Features

- **Works on any device** — phone, tablet, laptop (same Wi‑Fi)
- **Login / Sign up** with a name and password  
- **Coin wallet** — earn coins from correct words  
- **Easy** — free, 10 words, 3 letters (+10 each)  
- **Normal** — unlock for **500 coins**, 10 words, 4 letters (+15 each)  
- **Hard** — unlock for **1,500 coins**, 12 words, 5–6 letters (+20 each)  
- **Top** — unlock for **5,000 coins**, 15 words, 7–8 letters (+35 each)  
- **Voice** (Chrome/Edge) + **tap-to-type** + on-screen A–Z keyboard  
- **Leaderboard** per mode  

## Run on your computer

```bash
cd kids-word-game
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000** on the computer.

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