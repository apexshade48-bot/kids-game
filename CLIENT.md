# Word Stars — Client Handoff Guide

This document is for **you (the client)** or whoever hosts the game.

## What you received

**Word Stars** is a kids word-learning game. Players sign up, earn coins, unlock levels, and compete on leaderboards. It runs as a small web server — not as files you copy to a tablet.

## Fastest way to run (Docker)

If Docker is installed:

```bash
docker compose up --build
```

Open **http://localhost:5000**

Data is saved in a Docker volume (`wordstars_data`).

### Before going live

1. Copy `.env.example` to `.env`
2. Set a strong `SECRET_KEY` (long random string)
3. Set `INITIAL_ADMIN_NAME` to the admin account name you want
4. Restart: `docker compose up --build`

---

## Without Docker (Windows)

1. Install [Python 3.11+](https://www.python.org/downloads/)
2. Double-click **`start-client.bat`**
3. Open **http://localhost:5000**

---

## Give players a public link (recommended)

For phones and tablets **anywhere** (not just your Wi‑Fi), host on the cloud:

### Option A — Render (free tier, easy)

1. Push this folder to a GitHub repo (do **not** commit `.env` or `kids_word_game.db`)
2. Go to [render.com](https://render.com) → New **Web Service**
3. Connect the repo
4. Settings:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app`
   - **Env vars:** `SECRET_KEY`, `BEHIND_PROXY=1`, `DATA_DIR=/tmp/data`
5. Deploy — Render gives you a URL like `https://word-stars.onrender.com`

### Option B — Railway / Fly.io / VPS

Same idea: Python app, start with gunicorn, set `SECRET_KEY` and `BEHIND_PROXY=1`.

### Option C — Your own server + domain

Run Docker or gunicorn behind **nginx** with **HTTPS**. Voice/mic works best with HTTPS on mobile.

---

## Admin access

1. Sign up with the name set in `INITIAL_ADMIN_NAME` (default: **Apex**)
2. Log in — you will see an **Admin** tab
3. From Admin you can:
   - Edit player coins
   - Grant level unlocks
   - Promote other admins (developers)
   - Reset scores or delete players

---

## Playing on tablets & phones

| Scenario | What to do |
|----------|------------|
| **Same Wi‑Fi as the server** | Open `http://SERVER-IP:5000` (shown when the server starts) |
| **Public cloud URL** | Share the `https://...` link — works on any device |
| **Do NOT** | Copy HTML files to a tablet — that will not work |

Help page on the site: `/devices`

---

## Support checklist

- [ ] `SECRET_KEY` set in production
- [ ] HTTPS enabled for public URL (voice on mobile)
- [ ] Admin account created and tested
- [ ] Database backed up (`kids_word_game.db` or Docker volume)
- [ ] Firewall allows port 5000 (if self-hosting)

---

## Files that matter

| File | Purpose |
|------|---------|
| `app.py` | Main application |
| `database.py` | Player data & scores |
| `kids_word_game.db` | Database (created automatically) |
| `.env` | Secrets & config (create from `.env.example`) |
| `docker-compose.yml` | One-command hosting |

Built by your developer. Version 2.2.