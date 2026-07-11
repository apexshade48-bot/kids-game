"""Kids Word Game — Flask app for ages 4–5."""

import os
import secrets

from functools import wraps

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
from words import MODE_CONFIG, MODE_ORDER, get_round_words, word_hint

APP_VERSION = "2.2"
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


@app.before_request
def ensure_db():
    if not getattr(app, "_db_ready", False):
        db.init_db()
        app._db_ready = True
    if login_required():
        session["is_admin"] = db.is_user_admin(session["user_id"])


@app.context_processor
def inject_globals():
    base = {
        "app_version": APP_VERSION,
        "device_urls": get_device_urls(PORT),
        "unlock_costs": db.UNLOCK_COSTS,
        "is_admin": False,
        "wallet": None,
    }
    if "user_id" in session:
        base["wallet"] = db.get_user_wallet(session["user_id"])
        base["is_admin"] = session.get("is_admin", False)
    return base


@app.after_request
def add_device_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=3600"
    return response


def login_required():
    return "user_id" in session


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not login_required():
            return redirect(url_for("login"))
        if not session.get("is_admin"):
            flash("Admin access only.", "error")
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
        ok, result = db.create_user(name, password)
        if not ok:
            flash(str(result), "error")
            return render_template("login.html", tab="signup", name=name)
        session["user_id"] = result
        session["user_name"] = name.strip()
        session["is_admin"] = db.is_user_admin(result)
        return redirect(url_for("home"))

    return render_template("login.html", tab="signup")


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
        return redirect(url_for("home"))

    return render_template("login.html", tab="login")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/home")
def home():
    if not login_required():
        return redirect(url_for("login"))
    scores = db.get_user_scores(session["user_id"])
    wallet = db.get_user_wallet(session["user_id"])
    return render_template(
        "home.html",
        name=session.get("user_name", "Friend"),
        scores=scores,
        modes=MODE_CONFIG,
        mode_order=MODE_ORDER,
        wallet=wallet,
        unlock_costs=db.UNLOCK_COSTS,
    )


@app.route("/play/<mode>")
def play(mode):
    if not login_required():
        return redirect(url_for("login"))
    if mode not in MODE_CONFIG:
        flash("Unknown mode.", "error")
        return redirect(url_for("home"))

    if not db.is_mode_unlocked(session["user_id"], mode):
        cost = db.UNLOCK_COSTS.get(mode, 0)
        flash(f"Unlock {MODE_CONFIG[mode]['label']} with {cost} coins first!", "error")
        return redirect(url_for("home"))

    words = get_round_words(mode)
    cfg = MODE_CONFIG[mode]
    round_data = [
        {"word": w, "hint": word_hint(w)} for w in words
    ]
    return render_template(
        "play.html",
        mode=mode,
        mode_label=cfg["label"],
        points_per_word=cfg["points"],
        words=round_data,
        name=session.get("user_name", "Friend"),
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
    if points < 1 or points > max_points:
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


@app.route("/leaderboard")
def leaderboard():
    if not login_required():
        return redirect(url_for("login"))
    mode = request.args.get("mode", "easy")
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
    )


@app.route("/admin")
@admin_required
def admin_panel():
    stats = db.get_admin_stats()
    users = db.get_all_users()
    admins = db.get_admin_users()
    return render_template(
        "admin.html",
        stats=stats,
        users=users,
        admins=admins,
        unlock_costs=db.UNLOCK_COSTS,
        name=session.get("user_name", "Admin"),
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


@app.route("/admin/api/user/<int:user_id>/reset", methods=["POST"])
@admin_required
def admin_api_reset_scores(user_id):
    ok, result = db.admin_reset_scores(user_id)
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


@app.route("/api/leaderboard/<mode>")
def api_leaderboard(mode):
    if not login_required():
        return jsonify({"error": "Not logged in"}), 401
    if mode not in MODE_CONFIG:
        return jsonify({"error": "Invalid mode"}), 400
    return jsonify(
        {
            "mode": mode,
            "board": db.get_leaderboard(mode),
            "current_user_id": session["user_id"],
        }
    )


if __name__ == "__main__":
    db.init_db()
    urls = get_device_urls(PORT)
    print("\n⭐ Word Stars is running!")
    print(f"   On this computer: http://127.0.0.1:{PORT}")
    if urls:
        print("   On tablet/phone (same Wi‑Fi):")
        for url in urls:
            print(f"   → {url}")
    else:
        print("   On tablet/phone: use this computer's Wi‑Fi IP address")
    print(f"   Device help: http://127.0.0.1:{PORT}/devices\n")
    app.run(debug=DEBUG, host="0.0.0.0", port=PORT)