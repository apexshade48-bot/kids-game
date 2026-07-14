# Deploy Word Stars for FREE

Best free options for your client (no credit card on some, $0/month).

**Current app version:** check `/healthz` after deploy (`{"ok":true,"version":"4.0"}`).

### Why cloud?
- Tablet works **anywhere** (no same-Wi‑Fi / firewall fight)
- **HTTPS** helps browser features (including mic on some devices)
- PC does not need to stay on

---

## Option 1 — PythonAnywhere (recommended, free forever)

**Why:** SQLite data **stays saved**. Works on phones/tablets via a public URL.  
**Cost:** $0 — free tier (renew every 3 months with one click).

### Steps

1. Sign up: [pythonanywhere.com/registration/](https://www.pythonanywhere.com/registration/)
2. Open **Files** → upload `word-stars-client.zip` → unzip to `/home/YOURUSERNAME/kids-word-game`
3. Open **Consoles** → **Bash**:
   ```bash
   cd ~/kids-word-game
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. Open **Web** → **Add a new web app** → **Manual configuration** → **Python 3.13**
5. **Code** section → **WSGI configuration file** → edit it to:

   ```python
   import os
   import sys

   project_home = "/home/YOURUSERNAME/kids-word-game"
   if project_home not in sys.path:
       sys.path.insert(0, project_home)

   os.environ["DATA_DIR"] = project_home
   os.environ["BEHIND_PROXY"] = "1"
   os.environ["SECRET_KEY"] = "paste-a-long-random-string-here"
   os.environ["INITIAL_ADMIN_NAME"] = "Apex"

   from wsgi import application
   ```

   Replace `YOURUSERNAME` with your PythonAnywhere username.

6. **Virtualenv:** `/home/YOURUSERNAME/kids-word-game/venv`
7. **Static files:**
   - URL: `/static/`
   - Directory: `/home/YOURUSERNAME/kids-word-game/static/`
8. Click **Reload**
9. Your live URL: `https://YOURUSERNAME.pythonanywhere.com`

Share that link with your client. Sign up as **Apex** (or your `INITIAL_ADMIN_NAME`) for admin access.

---

## Option 2 — Render (easy, but data can reset)

**Why:** Connect GitHub, auto-deploy.  
**Cost:** $0 free tier.  
**Catch:** Free instances sleep after ~15 min idle; SQLite may reset on redeploy.

### Steps

1. Create a GitHub repo and push this folder (see below).
2. Go to [render.com](https://render.com) → sign up free.
3. **New** → **Blueprint** → connect repo → uses `render.yaml` automatically.
4. Deploy. URL will be like `https://word-stars-xxxx.onrender.com`.

Good for demos; for a long-term client, use PythonAnywhere or Fly.io with a volume.

---

## Option 3 — Fly.io (free credits, persistent data)

**Why:** Docker + saved database volume.  
**Cost:** $0 within free allowance (check [fly.io/docs/about/pricing](https://fly.io/docs/about/pricing)).

```bash
# Install flyctl, then:
cd kids-word-game
fly launch --no-deploy
fly volumes create wordstars_data --size 1 --region iad
fly secrets set SECRET_KEY=your-long-random-secret INITIAL_ADMIN_NAME=Apex
fly deploy
```

---

## Push to GitHub (for Render)

In the project folder:

```bash
git init
git add .
git commit -m "Word Stars client app"
# Create empty repo on github.com, then:
git remote add origin https://github.com/YOURNAME/word-stars.git
git push -u origin main
```

---

## What to send your client

One link, for example:

- `https://yourname.pythonanywhere.com` (PythonAnywhere)
- `https://word-stars-xxxx.onrender.com` (Render)

Tell them: open in Chrome or Safari, sign up, play. Admin account name: **Apex** (or whatever you set).

---

## Free tier comparison

| Host | Cost | Data saved? | Sleeps? | Best for |
|------|------|-------------|---------|----------|
| PythonAnywhere | $0 | Yes | No | **Client production** |
| Render | $0 | Risky | Yes (~15 min) | Quick demo |
| Fly.io | $0* | Yes (volume) | Can stop | Tech-savvy deploy |
| Your PC + Wi‑Fi | $0 | Yes | PC must stay on | Home / classroom |

\* Within free credit limits