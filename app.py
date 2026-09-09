"""Kids Word Game — Flask app for ages 4–5."""

import os
import secrets
from functools import wraps

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import database as db
from network import DEFAULT_PORT, get_device_urls
from words import (
    MODE_CONFIG,
    MODE_ORDER,
    get_picture_quiz_questions,
    get_quiz_questions,
    get_round_words,
    word_hint,
)

APP_VERSION = "6.6"
PORT = int(os.environ.get("PORT", DEFAULT_PORT))
DEBUG = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
BEHIND_PROXY = os.environ.get("BEHIND_PROXY", "0").lower() in ("1", "true", "yes")

_secret = os.environ.get("SECRET_KEY")
if not _secret:
    _secret = secrets.token_hex(32)
    if not DEBUG:
        print("WARNING: Set SECRET_KEY in production (sessions reset on restart).")

app = Flask(__name__)
app.secret_key = _secret
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=BEHIND_PROXY,
    PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30,
)
if BEHIND_PROXY:
    from werkzeug.middleware.proxy_fix import ProxyFix

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)


def login_required():
    return "user_id" in session


@app.before_request
def ensure_db():
    if not getattr(app, "_db_ready", False):
        db.init_db()
        app._db_ready = True
    if login_required():
        session["is_admin"] = db.is_user_admin(session["user_id"])
        session["is_owner"] = db.is_owner_admin_name(session.get("user_name", ""))
        session["god_mode"] = db.is_user_god(session["user_id"])
        session["is_hacker"] = db.is_user_hacker(session["user_id"])
        # Keep aura in session; force choose if missing (existing accounts)
        if not session.get("aura"):
            aura = db.get_user_aura(session["user_id"])
            if aura:
                session["aura"] = aura
            else:
                ep = request.endpoint or ""
                allowed = {
                    "choose_aura",
                    "logout",
                    "static",
                    "healthz",
                    "devices_help",
                    "api_set_aura",
                    "privacy",
                    "assetlinks",
                }
                if ep not in allowed and not str(request.path).startswith("/static"):
                    return redirect(url_for("choose_aura"))


@app.context_processor
def inject_globals():
    base = {
        "app_version": APP_VERSION,
        "device_urls": get_device_urls(PORT),
        "unlock_costs": db.UNLOCK_COSTS,
        "is_admin": False,
        "is_owner": False,
        "is_hacker": False,
        "wallet": None,
        "user_aura": None,
        "aura_choices": db.AURA_CHOICES,
        "avatar": None,
    }
    if "user_id" in session:
        base["wallet"] = db.get_user_wallet(session["user_id"])
        base["is_admin"] = session.get("is_admin", False)
        base["is_owner"] = session.get("is_owner", False)
        base["god_mode"] = session.get("god_mode", False)
        base["is_hacker"] = session.get("is_hacker", False) or session.get("is_owner", False)
        aura = session.get("aura") or db.get_user_aura(session["user_id"])
        base["user_aura"] = aura
        base["avatar"] = db.get_avatar(session["user_id"])
        if aura:
            session["aura"] = aura
    return base


@app.after_request
def add_device_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Permissions-Policy"] = "microphone=(self)"
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=3600"
    return response


def _wants_json():
    if request.path.startswith("/api/") or "/api/" in request.path:
        return True
    if request.accept_mimetypes.best == "application/json":
        return True
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    if request.is_json:
        return True
    ct = (request.content_type or "").lower()
    if "application/json" in ct:
        return True
    return False


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not login_required():
            if _wants_json():
                return jsonify({"error": "Not logged in. Please log in again."}), 401
            return redirect(url_for("login"))
        if not session.get("is_admin"):
            if _wants_json():
                return jsonify({"error": "Admin access only."}), 403
            flash("Admin access only.", "error")
            return redirect(url_for("home"))
        return f(*args, **kwargs)

    return wrapped


def owner_required(f):
    """Apex Shade — owner only (INITIAL_ADMIN_NAME)."""

    @wraps(f)
    def wrapped(*args, **kwargs):
        if not login_required():
            if _wants_json():
                return jsonify({"error": "Not logged in."}), 401
            return redirect(url_for("login"))
        name = session.get("user_name", "")
        if not db.is_owner_admin_name(name):
            if _wants_json():
                return jsonify({"error": "Apex Shade only."}), 403
            flash("Apex Shade only.", "error")
            return redirect(url_for("home"))
        return f(*args, **kwargs)

    return wrapped


def hacker_required(f):
    """Owner or a player gifted the Hacker Panel."""

    @wraps(f)
    def wrapped(*args, **kwargs):
        if not login_required():
            if _wants_json():
                return jsonify({"error": "Not logged in."}), 401
            return redirect(url_for("login"))
        if not (
            session.get("is_hacker")
            or session.get("is_owner")
            or db.is_user_hacker(session["user_id"])
        ):
            if _wants_json():
                return jsonify({"error": "Hacker Panel is gift-only."}), 403
            flash("Hacker Panel is gift-only. Ask Apex.", "error")
            return redirect(url_for("home"))
        return f(*args, **kwargs)

    return wrapped


@app.route("/devices")
def devices_help():
    return render_template(
        "devices.html",
        device_urls=get_device_urls(PORT),
        port=PORT,
    )


@app.route("/healthz")
def healthz():
    return jsonify({"ok": True, "version": APP_VERSION}), 200


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/.well-known/assetlinks.json")
def assetlinks():
    """Digital Asset Links for a Play Store Trusted Web Activity."""
    sha = (os.environ.get("ANDROID_CERT_SHA256") or "").strip()
    package = os.environ.get("ANDROID_PACKAGE", "com.wordstars.app")
    if not sha:
        return jsonify([]), 200
    return jsonify(
        [
            {
                "relation": ["delegate_permission/common.handle_all_urls"],
                "target": {
                    "namespace": "android_app",
                    "package_name": package,
                    "sha256_cert_fingerprints": [sha],
                },
            }
        ]
    )


@app.route("/")
def index():
    if login_required():
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if login_required():
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name", "")
        password = request.form.get("password", "")
        aura = request.form.get("aura", "")
        ok, result = db.create_user(name, password, aura=aura)
        if not ok:
            flash(str(result), "error")
            return render_template(
                "login.html",
                tab="signup",
                name=name,
                selected_aura=aura,
                aura_choices=db.AURA_CHOICES,
            )
        session["user_id"] = result
        session["user_name"] = name.strip()
        session["is_admin"] = db.is_user_admin(result)
        session["aura"] = db.normalize_aura(aura)
        return redirect(url_for("home"))

    return render_template(
        "login.html", tab="signup", aura_choices=db.AURA_CHOICES
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if login_required():
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name", "")
        password = request.form.get("password", "")
        ok, result = db.verify_user(name, password)
        if not ok:
            flash(str(result), "error")
            return render_template("login.html", tab="login", name=name)
        session["user_id"] = result["id"]
        session["user_name"] = result["name"]
        session["is_admin"] = result.get("is_admin", False)
        session["is_owner"] = db.is_owner_admin_name(result["name"])
        session["god_mode"] = result.get("god_mode", False)
        session["is_hacker"] = result.get("is_hacker", False) or db.is_owner_admin_name(
            result["name"]
        )
        session["aura"] = result.get("aura")
        if not result.get("aura"):
            return redirect(url_for("choose_aura"))
        return redirect(url_for("home"))

    return render_template("login.html", tab="login")


@app.route("/choose-aura", methods=["GET", "POST"])
def choose_aura():
    """Existing accounts without an aura must pick one."""
    if not login_required():
        return redirect(url_for("login"))
    current = db.get_user_aura(session["user_id"])
    if request.method == "POST":
        aura = request.form.get("aura", "")
        ok, result = db.set_user_aura(session["user_id"], aura)
        if not ok:
            flash(str(result), "error")
            return render_template(
                "choose_aura.html",
                aura_choices=db.AURA_CHOICES,
                selected_aura=aura,
                name=session.get("user_name", "Friend"),
                forced=not current,
            )
        session["aura"] = result
        flash("Aura saved! Your look is ready.", "success")
        return redirect(url_for("home"))

    # Already has aura — allow change anytime
    return render_template(
        "choose_aura.html",
        aura_choices=db.AURA_CHOICES,
        selected_aura=current or session.get("aura"),
        name=session.get("user_name", "Friend"),
        forced=not current,
    )


@app.route("/api/aura", methods=["POST"])
def api_set_aura():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    aura = data.get("aura") or ""
    ok, result = db.set_user_aura(session["user_id"], aura)
    if not ok:
        return jsonify({"error": result}), 400
    session["aura"] = result
    return jsonify({"ok": True, "aura": result})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/home")
def home():
    if not login_required():
        return redirect(url_for("login"))
    if not db.get_user_aura(session["user_id"]):
        return redirect(url_for("choose_aura"))
    scores = db.get_user_scores(session["user_id"])
    streak_bonus = db.claim_streak_bonus(session["user_id"])
    wallet = db.get_user_wallet(session["user_id"])
    progress = db.get_user_progress(session["user_id"])
    spin = db.get_spin_status(session["user_id"])
    if streak_bonus.get("granted"):
        flash(
            f"🔥 {streak_bonus['streak']}-day streak! +{streak_bonus['amount']} coins.",
            "success",
        )
    return render_template(
        "home.html",
        name=session.get("user_name", "Friend"),
        scores=scores,
        modes=MODE_CONFIG,
        mode_order=MODE_ORDER,
        wallet=wallet,
        unlock_costs=db.UNLOCK_COSTS,
        progress=progress,
        hint_cost=db.HINT_COST,
        spin=spin,
        streak_bonus=streak_bonus,
        avatar=db.get_avatar(session["user_id"]),
    )


@app.route("/shop")
def shop_page():
    if not login_required():
        return redirect(url_for("login"))
    catalog = db.get_shop_catalog(session["user_id"])
    market = db.get_player_market(session["user_id"])
    return render_template(
        "shop.html",
        name=session.get("user_name", "Friend"),
        catalog=catalog,
        market=market,
    )


@app.route("/api/shop/buy", methods=["POST"])
def api_shop_buy():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    item_id = (data.get("item_id") or "").strip()
    ok, result = db.buy_shop_item(session["user_id"], item_id)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, **result})


@app.route("/space")
def space_run():
    if not login_required():
        return redirect(url_for("login"))
    return render_template(
        "space.html",
        name=session.get("user_name", "Friend"),
        avatar=db.get_avatar(session["user_id"]),
    )


@app.route("/api/shop/list", methods=["POST"])
def api_shop_list():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    item_id = (data.get("item_id") or "").strip()
    ok, result = db.list_item_for_sale(
        session["user_id"], item_id, data.get("price")
    )
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, **result})


@app.route("/api/shop/unlist", methods=["POST"])
def api_shop_unlist():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    try:
        listing_id = int(data.get("listing_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "Missing listing"}), 400
    ok, result = db.unlist_item(session["user_id"], listing_id)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, **result})


@app.route("/api/shop/buy-player", methods=["POST"])
def api_shop_buy_player():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    try:
        listing_id = int(data.get("listing_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "Missing listing"}), 400
    ok, result = db.buy_player_listing(session["user_id"], listing_id)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, **result})


@app.route("/api/shop/equip", methods=["POST"])
def api_shop_equip():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    item_id = (data.get("item_id") or "").strip()
    ok, result = db.equip_shop_item(session["user_id"], item_id)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, **result})


@app.route("/player/<int:user_id>")
def player_profile(user_id):
    if not login_required():
        return redirect(url_for("login"))
    profile = db.get_player_profile(user_id)
    if not profile:
        flash("That Apex ID is gone.", "error")
        return redirect(url_for("leaderboard"))
    return render_template(
        "profile.html",
        profile=profile,
        is_self=user_id == session["user_id"],
        modes=MODE_CONFIG,
        mode_order=MODE_ORDER,
    )


@app.route("/chat")
def chat_page():
    if not login_required():
        return redirect(url_for("login"))
    with_id = request.args.get("with", type=int)
    other = db.get_player_profile(with_id) if with_id else None
    if with_id and not other:
        flash("That player is gone.", "error")
        return redirect(url_for("chat_page"))
    return render_template(
        "chat.html",
        other=other,
        with_id=with_id if other else None,
        name=session.get("user_name", "Friend"),
    )


@app.route("/api/chat", methods=["GET"])
def api_chat_list():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    after_id = request.args.get("after", default=0, type=int) or 0
    with_id = request.args.get("with", default=None, type=int)
    messages = db.get_chat_messages(
        session["user_id"], with_user_id=with_id, after_id=after_id
    )
    return jsonify({"ok": True, "messages": messages})


@app.route("/api/chat", methods=["POST"])
def api_chat_send():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    to_user_id = data.get("to")
    if to_user_id in ("", None):
        to_user_id = None
    ok, result = db.post_chat(session["user_id"], data.get("body") or "", to_user_id)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, "message": result})


def _require_unlocked_mode(mode: str):
    if mode not in MODE_CONFIG:
        flash("Unknown mode.", "error")
        return None, redirect(url_for("home"))
    if not db.is_mode_unlocked(session["user_id"], mode):
        cost = db.UNLOCK_COSTS.get(mode, 0)
        flash(f"Unlock {MODE_CONFIG[mode]['label']} with {cost} coins first!", "error")
        return None, redirect(url_for("home"))
    return MODE_CONFIG[mode], None


@app.route("/play/<mode>")
def play(mode):
    if not login_required():
        return redirect(url_for("login"))
    cfg, err = _require_unlocked_mode(mode)
    if err:
        return err

    words = get_round_words(mode)
    round_data = [{"word": w, "hint": word_hint(w)} for w in words]
    hide_word = bool(cfg.get("hide_word")) and not cfg.get("phrases")
    return render_template(
        "play.html",
        mode=mode,
        mode_label=cfg["label"],
        points_per_word=cfg["points"],
        words=round_data,
        hint_cost=db.HINT_COST,
        speak_focus=bool(cfg.get("speak_focus")),
        hide_word=hide_word,
        mode_blurb=cfg.get("blurb") or "",
        name=session.get("user_name", "Friend"),
    )


@app.route("/quiz/<mode>")
def quiz(mode):
    """Missing-letter quiz (default)."""
    if not login_required():
        return redirect(url_for("login"))
    cfg, err = _require_unlocked_mode(mode)
    if err:
        return err
    if cfg.get("phrases"):
        flash("Family Speak is voice practice — use Speak, not Quiz.", "error")
        return redirect(url_for("play", mode=mode))

    questions = get_quiz_questions(mode)
    return render_template(
        "quiz.html",
        mode=mode,
        mode_label=cfg["label"],
        points_per_word=cfg["points"],
        questions=questions,
        quiz_kind="letter",
        name=session.get("user_name", "Friend"),
    )


@app.route("/pics/<mode>")
def pics_quiz(mode):
    """Picture quiz: emoji → pick the word."""
    if not login_required():
        return redirect(url_for("login"))
    cfg, err = _require_unlocked_mode(mode)
    if err:
        return err
    if cfg.get("phrases"):
        flash("Family Speak is voice practice — use Speak, not Pics.", "error")
        return redirect(url_for("play", mode=mode))

    questions = get_picture_quiz_questions(mode)
    return render_template(
        "quiz.html",
        mode=mode,
        mode_label=cfg["label"],
        points_per_word=cfg["points"],
        questions=questions,
        quiz_kind="picture",
        name=session.get("user_name", "Friend"),
    )


@app.route("/api/hint", methods=["POST"])
def api_hint():
    """Spend coins to reveal the first letter of the current spell word (client applies)."""
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")
    word = (data.get("word") or "").strip().lower()
    if mode not in MODE_CONFIG:
        return jsonify({"error": "Invalid mode"}), 400
    if not db.is_mode_unlocked(session["user_id"], mode):
        return jsonify({"error": "Mode locked"}), 403
    if not word or len(word) < 1:
        return jsonify({"error": "Missing word"}), 400
    ok, result = db.spend_coins(session["user_id"], db.HINT_COST)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify(
        {
            "ok": True,
            "hint_letter": word[0].upper(),
            "coins": result,
            "cost": db.HINT_COST,
        }
    )


@app.route("/api/score", methods=["POST"])
def api_score():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    mode = data.get("mode")
    points = data.get("points")

    if mode not in MODE_CONFIG:
        return jsonify({"error": "Invalid mode"}), 400
    if not db.is_mode_unlocked(session["user_id"], mode):
        return jsonify({"error": "Mode locked"}), 403
    try:
        points = int(points)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid points"}), 400

    max_points = MODE_CONFIG[mode]["points"]
    god = db.is_user_god(session["user_id"])
    if god:
        # Apex Shade God Mode: allow big injections from play; min 1
        if points < 1:
            return jsonify({"error": "Invalid points amount"}), 400
        points = min(points, 99999)
    elif points < 1 or points > max_points:
        return jsonify({"error": "Invalid points amount"}), 400

    total = db.add_points(session["user_id"], mode, points)
    coins = db.add_coins(session["user_id"], points)
    return jsonify({"ok": True, "total": total, "coins": coins, "mode": mode})


@app.route("/api/unlock", methods=["POST"])
def api_unlock():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    mode = data.get("mode")
    if mode not in db.UNLOCK_COSTS:
        return jsonify({"error": "Invalid mode"}), 400

    ok, result = db.unlock_mode(session["user_id"], mode)
    if not ok:
        return jsonify({"error": result}), 400

    return jsonify({"ok": True, "wallet": result, "mode": mode})


# ── 2-player battle (hot-seat on same device) ───────────────────────────

BATTLE_ROUNDS_DEFAULT = 6
BATTLE_WIN_COINS = 50


@app.route("/battle", methods=["GET", "POST"])
def battle_setup():
    if not login_required():
        return redirect(url_for("login"))
    wallet = db.get_user_wallet(session["user_id"])
    if request.method == "POST":
        p2 = (request.form.get("player2") or "").strip()
        mode = (request.form.get("mode") or "easy").strip().lower()
        try:
            rounds = int(request.form.get("rounds") or BATTLE_ROUNDS_DEFAULT)
        except (TypeError, ValueError):
            rounds = BATTLE_ROUNDS_DEFAULT
        rounds = max(3, min(rounds, 12))

        if not p2 or len(p2) > 24:
            flash("Enter player 2’s name (max 24 letters).", "error")
            return redirect(url_for("battle_setup"))
        if p2.lower() == (session.get("user_name") or "").lower():
            flash("Player 2 needs a different name.", "error")
            return redirect(url_for("battle_setup"))
        if mode not in MODE_CONFIG:
            mode = "easy"
        if not db.is_mode_unlocked(session["user_id"], mode):
            flash("Unlock that mode first (for the host).", "error")
            return redirect(url_for("battle_setup"))

        # Shared word list — both players face the same words in turn order
        import random as _rnd

        pool_words = []
        for _ in range(4):
            pool_words.extend(get_round_words(mode))
        # unique preserve order
        seen = set()
        words = []
        for w in pool_words:
            if w not in seen:
                seen.add(w)
                words.append(w)
            if len(words) >= rounds:
                break
        if len(words) < rounds:
            words = (words * ((rounds // max(len(words), 1)) + 1))[:rounds]
        else:
            words = words[:rounds]
        _rnd.shuffle(words)

        session["battle"] = {
            "p1_name": session.get("user_name", "Player 1"),
            "p1_id": session["user_id"],
            "p2_name": p2,
            "mode": mode,
            "words": [{"word": w, "hint": word_hint(w)} for w in words],
            "index": 0,
            "turn": 1,  # 1 or 2
            "p1_score": 0,
            "p2_score": 0,
            "points_per": MODE_CONFIG[mode]["points"],
            "done": False,
            "winner": None,
        }
        return redirect(url_for("battle_play"))

    unlocked = [m for m in MODE_ORDER if wallet["unlocked"].get(m)]
    if not unlocked:
        unlocked = ["easy"]
    return render_template(
        "battle.html",
        unlocked=unlocked,
        modes=MODE_CONFIG,
        name=session.get("user_name", "Friend"),
        win_coins=BATTLE_WIN_COINS,
        default_rounds=BATTLE_ROUNDS_DEFAULT,
    )


@app.route("/battle/play")
def battle_play():
    if not login_required():
        return redirect(url_for("login"))
    battle = session.get("battle")
    if not battle:
        flash("Start a battle first.", "error")
        return redirect(url_for("battle_setup"))
    return render_template(
        "battle_play.html",
        battle=battle,
        win_coins=BATTLE_WIN_COINS,
    )


@app.route("/api/battle/answer", methods=["POST"])
def api_battle_answer():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    battle = session.get("battle")
    if not battle or battle.get("done"):
        return jsonify({"error": "No active battle."}), 400

    data = request.get_json(silent=True) or {}
    answer = (data.get("answer") or "").strip().lower()
    answer = "".join(c for c in answer if c.isalpha())

    words = battle.get("words") or []
    idx = int(battle.get("index") or 0)
    if idx >= len(words):
        return jsonify({"error": "Battle already finished."}), 400

    want = (words[idx].get("word") or "").lower()
    turn = int(battle.get("turn") or 1)
    correct = answer == want

    if correct:
        if turn == 1:
            battle["p1_score"] = int(battle.get("p1_score") or 0) + 1
        else:
            battle["p2_score"] = int(battle.get("p2_score") or 0) + 1

    # Advance: after each attempt (correct or not), next turn / word
    # Each word is attempted by one player (current turn), then next word + swap turn
    battle["index"] = idx + 1
    battle["turn"] = 2 if turn == 1 else 1

    reward = 0
    winner = None
    if battle["index"] >= len(words):
        battle["done"] = True
        s1 = int(battle["p1_score"])
        s2 = int(battle["p2_score"])
        if s1 > s2:
            winner = "p1"
            battle["winner"] = battle["p1_name"]
            # Host (logged-in) gets win coins
            if battle.get("p1_id") == session["user_id"]:
                reward = BATTLE_WIN_COINS
                db.add_coins(session["user_id"], reward)
        elif s2 > s1:
            winner = "p2"
            battle["winner"] = battle["p2_name"]
        else:
            winner = "draw"
            battle["winner"] = None
            # Draw: small reward for host
            if battle.get("p1_id") == session["user_id"]:
                reward = 15
                db.add_coins(session["user_id"], reward)

    session["battle"] = battle
    session.modified = True

    next_word = None
    if not battle["done"] and battle["index"] < len(words):
        nw = words[battle["index"]]
        next_word = {"word": nw["word"], "hint": nw.get("hint") or "✨"}

    coins = db.get_user_coins(session["user_id"])
    return jsonify(
        {
            "ok": True,
            "correct": correct,
            "want": want,
            "p1_score": battle["p1_score"],
            "p2_score": battle["p2_score"],
            "turn": battle["turn"],
            "index": battle["index"],
            "total": len(words),
            "done": battle["done"],
            "winner": winner,
            "winner_name": battle.get("winner"),
            "reward": reward,
            "coins": coins,
            "next": next_word,
            "p1_name": battle["p1_name"],
            "p2_name": battle["p2_name"],
        }
    )


@app.route("/api/battle/cancel", methods=["POST"])
def api_battle_cancel():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    session.pop("battle", None)
    return jsonify({"ok": True})


@app.route("/spin")
def lucky_spin_page():
    if not login_required():
        return redirect(url_for("login"))
    status = db.get_spin_status(session["user_id"])
    return render_template(
        "spin.html",
        spin=status,
        name=session.get("user_name", "Friend"),
    )


@app.route("/api/spin", methods=["POST"])
def api_lucky_spin():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json(silent=True) or {}
    use_paid = bool(data.get("paid"))
    ok, result = db.do_lucky_spin(session["user_id"], use_paid=use_paid)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, **result})


@app.route("/api/spin/status")
def api_spin_status():
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    return jsonify({"ok": True, **db.get_spin_status(session["user_id"])})


@app.route("/leaderboard")
def leaderboard():
    if not login_required():
        return redirect(url_for("login"))
    mode = request.args.get("mode", "easy")
    if mode == "coins":
        board = db.get_coins_leaderboard()
        return render_template(
            "leaderboard.html",
            mode="coins",
            board=board,
            modes=MODE_CONFIG,
            current_user_id=session["user_id"],
            name=session.get("user_name", "Friend"),
            board_kind="coins",
        )
    if mode not in MODE_CONFIG:
        mode = "easy"
    board = db.get_leaderboard(mode)
    return render_template(
        "leaderboard.html",
        mode=mode,
        board=board,
        modes=MODE_CONFIG,
        current_user_id=session["user_id"],
        name=session.get("user_name", "Friend"),
        board_kind="stars",
    )


@app.route("/admin")
@admin_required
def admin_panel():
    stats = db.get_admin_stats()
    users = db.get_all_users_progress()
    admins = db.get_admin_users()
    user_name = session.get("user_name", "")
    return render_template(
        "admin.html",
        stats=stats,
        users=users,
        admins=admins,
        unlock_costs=db.UNLOCK_COSTS,
        name=user_name or "Admin",
        is_owner=db.is_owner_admin_name(user_name),
    )


@app.route("/admin/api/users")
@admin_required
def admin_api_users():
    return jsonify({"users": db.get_all_users(), "stats": db.get_admin_stats()})


@app.route("/admin/api/user/<int:user_id>/coins", methods=["POST"])
@admin_required
def admin_api_set_coins(user_id):
    data = request.get_json(silent=True) or {}
    try:
        coins = int(data.get("coins", -1))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid coins"}), 400
    ok, result = db.admin_set_coins(user_id, coins)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, "coins": result})


@app.route("/admin/api/user/<int:user_id>/unlock", methods=["POST"])
@admin_required
def admin_api_grant_unlock(user_id):
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")
    ok, result = db.admin_grant_unlock(user_id, mode)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, "message": result})


@app.route("/admin/api/user/<int:user_id>/lock", methods=["POST"])
@admin_required
def admin_api_lock_mode(user_id):
    """Lock Normal / Hard / Top (or all paid modes) for a player."""
    data = request.get_json(silent=True) or {}
    mode = (data.get("mode") or "").strip().lower()
    if mode == "all":
        ok, result = db.admin_lock_all_paid_modes(user_id)
    else:
        ok, result = db.admin_revoke_unlock(user_id, mode)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, "message": result})


@app.route("/admin/api/user/<int:user_id>/reset", methods=["POST"])
@admin_required
def admin_api_reset_scores(user_id):
    ok, result = db.admin_reset_scores(user_id)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, "message": result})


@app.route("/admin/api/user/<int:user_id>/password", methods=["POST"])
@admin_required
def admin_api_set_password(user_id):
    data = request.get_json(silent=True) or {}
    password = data.get("password") or ""
    ok, result = db.admin_set_password(user_id, password)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, "message": result})


@app.route("/admin/api/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_api_delete_user(user_id):
    if user_id == session["user_id"]:
        return jsonify({"error": "Cannot delete your own account."}), 400
    ok, result = db.admin_delete_user(user_id)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, "message": result})


@app.route("/admin/api/user/<int:user_id>/role", methods=["POST"])
@admin_required
def admin_api_set_role(user_id):
    data = request.get_json(silent=True) or {}
    if "is_admin" not in data:
        return jsonify({"error": "Missing is_admin"}), 400
    is_admin = bool(data["is_admin"])
    ok, result = db.admin_set_admin_role(user_id, is_admin, session["user_id"])
    if not ok:
        return jsonify({"error": result}), 400
    if user_id == session["user_id"]:
        session["is_admin"] = is_admin
    return jsonify({"ok": True, "user": result})


@app.route("/shade")
@owner_required
def apex_shade():
    """Apex Shade control room — owner only."""
    users = db.get_all_users()
    god = db.is_user_god(session["user_id"])
    return render_template(
        "shade.html",
        users=users,
        god_mode=god,
        name=session.get("user_name", "Apex"),
        stats=db.get_admin_stats(),
    )


@app.route("/shade/api/<action>", methods=["POST"])
@owner_required
def shade_api(action):
    uid = session["user_id"]
    data = request.get_json(silent=True) or {}
    action = (action or "").strip().lower()

    if action == "god_on":
        ok, msg = db.set_god_mode(uid, True)
    elif action == "god_off":
        ok, msg = db.set_god_mode(uid, False)
    elif action == "nuke_points":
        ok, msg = db.shade_nuke_all_points()
    elif action == "purge_players":
        ok, msg = db.shade_purge_players(uid)
    elif action == "scorch_board":
        ok, msg = db.shade_scorch_leaderboard()
    elif action == "factory_death":
        ok, msg = db.shade_factory_reset(uid)
    elif action == "boost_mega":
        ok, msg = db.shade_inject_stats(uid, coins=99999, points_per_mode=99999)
        if ok:
            db.shade_unlock_all(uid)
    elif action == "unlock_all":
        ok, msg = db.shade_unlock_all(uid)
    elif action == "path_win":
        ok, msg = db.shade_inject_stats(uid, coins=50000, points_per_mode=50000)
        if ok:
            db.shade_unlock_all(uid)
            msg = "Instant path win — all modes maxed."
    elif action == "immortal":
        # “Lives” → huge coin pool for hints / unlocks
        ok, msg = db.shade_inject_stats(uid, coins=999999)
        if ok:
            msg = "Immortal pool: 999999 coins."
    elif action == "reset_me":
        ok, msg = db.shade_reset_my_run(uid)
        session["god_mode"] = False
    elif action == "inject":
        try:
            coins = int(data.get("coins", 0))
            points = int(data.get("points", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid numbers"}), 400
        ok, msg = db.shade_inject_stats(
            uid, coins=coins if coins >= 0 else None, points_per_mode=points if points >= 0 else None
        )
    elif action == "force_first":
        ok, msg = db.shade_force_rank_one(uid)
    elif action == "crush":
        name = (data.get("name") or "").strip()
        target = db.shade_find_user_by_name(name)
        if not target:
            return jsonify({"error": "Player not found."}), 404
        ok, msg = db.shade_crush_points(target["id"])
    elif action == "ban":
        name = (data.get("name") or "").strip()
        target = db.shade_find_user_by_name(name)
        if not target:
            return jsonify({"error": "Player not found."}), 404
        ok, msg = db.shade_ban_user(target["id"], True)
    elif action == "delete":
        name = (data.get("name") or "").strip()
        target = db.shade_find_user_by_name(name)
        if not target:
            return jsonify({"error": "Player not found."}), 404
        ok, msg = db.shade_delete_user(target["id"])
    elif action == "gift_hacker":
        name = (data.get("name") or "").strip()
        target = db.shade_find_user_by_name(name)
        if not target:
            return jsonify({"error": "Player not found."}), 404
        ok, msg = db.set_user_hacker(target["id"], True)
    elif action == "revoke_hacker":
        name = (data.get("name") or "").strip()
        target = db.shade_find_user_by_name(name)
        if not target:
            return jsonify({"error": "Player not found."}), 404
        ok, msg = db.set_user_hacker(target["id"], False)
    elif action == "strip_admin":
        name = (data.get("name") or "").strip()
        target = db.shade_find_user_by_name(name)
        if not target:
            return jsonify({"error": "Player not found."}), 404
        ok, msg = db.strip_admin_gear(target["id"])
    elif action == "gift_admin":
        name = (data.get("name") or "").strip()
        target = db.shade_find_user_by_name(name)
        if not target:
            return jsonify({"error": "Player not found."}), 404
        ok, msg = db.gift_admin_gear(target["id"])
    elif action == "dump":
        return jsonify({"ok": True, "dump": db.shade_system_dump()})
    elif action == "spawn_fakes":
        ok, msg = db.shade_spawn_fakes(int(data.get("count", 5) or 5))
    elif action == "clear_fakes":
        ok, msg = db.shade_clear_fakes()
    elif action == "players":
        return jsonify({"ok": True, "users": db.get_all_users()})
    else:
        return jsonify({"error": "Unknown shade action."}), 400

    if not ok:
        return jsonify({"error": msg}), 400
    session["god_mode"] = db.is_user_god(uid)
    return jsonify({"ok": True, "message": msg, "god_mode": session["god_mode"]})


@app.route("/hacker")
@hacker_required
def hacker_panel():
    wallet = db.get_user_wallet(session["user_id"])
    return render_template(
        "hacker.html",
        name=session.get("user_name", "Hacker"),
        wallet=wallet,
        is_owner=session.get("is_owner", False),
    )


@app.route("/hacker/api/<action>", methods=["POST"])
@hacker_required
def hacker_api(action):
    uid = session["user_id"]
    data = request.get_json(silent=True) or {}
    action = (action or "").strip().lower()

    if action == "coins":
        ok, msg = db.hacker_add_coins(uid, data.get("amount") or 0)
    elif action == "unlock_all":
        ok, msg = db.shade_unlock_all(uid)
    elif action == "stars":
        ok, msg = db.shade_inject_stats(uid, points_per_mode=99999)
        if ok:
            msg = "Stars maxed in every mode."
    elif action == "bank":
        ok, msg = db.shade_inject_stats(uid, coins=1_000_000_000_000_000)
        if ok:
            msg = "Hacker bank: 1Q coins."
    elif action == "path_win":
        ok, msg = db.shade_inject_stats(uid, coins=1_000_000, points_per_mode=50000)
        if ok:
            db.shade_unlock_all(uid)
            msg = "Path win — modes unlocked, coins & stars boosted."
    else:
        return jsonify({"error": "Unknown hack."}), 400

    if not ok:
        return jsonify({"error": msg}), 400
    wallet = db.get_user_wallet(uid)
    return jsonify({"ok": True, "message": msg, "coins": wallet["coins"]})


@app.route("/api/leaderboard/<mode>")
def api_leaderboard(mode):
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    if mode == "coins":
        return jsonify({"mode": "coins", "board": db.get_coins_leaderboard()})
    if mode not in MODE_CONFIG:
        return jsonify({"error": "Invalid mode"}), 400
    return jsonify({"mode": mode, "board": db.get_leaderboard(mode)})


if __name__ == "__main__":
    urls = get_device_urls(PORT)
    print("\n⭐ Word Stars")
    print(f"   On this computer: http://127.0.0.1:{PORT}")
    if urls:
        print("   On phone/tablet (same Wi‑Fi):")
        for u in urls:
            print(f"   {u}")
    print(f"   Device help: http://127.0.0.1:{PORT}/devices\n")
    app.run(debug=DEBUG, host="0.0.0.0", port=PORT)
