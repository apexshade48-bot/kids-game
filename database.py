"""SQLite helpers for users, mode scores, coins, and unlocks."""

import os
import secrets
import sqlite3
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

import re

from shop import (
    ADMIN_ITEM_IDS,
    ADMIN_OWNER_LIMIT,
    DEV_ITEM_IDS,
    DEV_OWNER_LIMIT,
    DEFAULT_HAT,
    DEFAULT_NAME,
    DEFAULT_PANTS,
    DEFAULT_SHIRT,
    cost_label,
    get_item,
    item_public,
    items_for_slot,
    name_style,
    slot_column,
)

_DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parent))
DB_PATH = _DATA_DIR / "kids_word_game.db"

# Letters/digits/spaces and a few basic punctuation marks only — this name is later
# interpolated into an email Subject header (mailer.py), so no control characters,
# no \r or \n, and no header-injection-friendly symbols.
_NAME_ALLOWED_RE = re.compile(r"^[\w' .\-]+$", re.UNICODE)

FREE_MODES = frozenset({"letters", "sounds", "beginner", "easy"})
UNLOCK_COSTS = {
    "normal": 300,
    "hard": 5000,
    "top": 10000,
    "impossible": 20000,  # family spoken English (admin can unlock for free)
}
ALL_MODES = (
    "letters",
    "sounds",
    "beginner",
    "easy",
    "normal",
    "hard",
    "top",
    "impossible",
)
LOCKED_MODES = tuple(m for m in ALL_MODES if m not in FREE_MODES)
MODE_SQL_LIST = (
    "'letters', 'sounds', 'beginner', 'easy', 'normal', 'hard', 'top', 'impossible'"
)
UNLOCK_SQL_LIST = "'normal', 'hard', 'top', 'impossible'"
HINT_COST = 5  # coins to reveal first letter in Spell mode
SPIN_COST = 150  # coins for an extra lucky spin (after free daily)
STREAK_BONUSES = {1: 10, 3: 25, 7: 50}  # coins on milestone streak days

# Account aura (theme/skin) — chosen at signup or first login
AURA_IDS = (
    "violet",
    "ocean",
    "forest",
    "sunset",
    "candy",
    "night",
    "aura",
    "rainbow",
    "beach",
    "snow",
    "meadow",
    "lemon",
    "bubble",
    "lava",
    "galaxy",
)
AURA_CHOICES = (
    {"id": "violet", "label": "Magic sky", "emoji": "💜", "dots": ("#7c3aed", "#f8fafc", "#f59e0b")},
    {"id": "ocean", "label": "Ocean", "emoji": "🌊", "dots": ("#0284c7", "#ecfeff", "#22d3ee")},
    {"id": "forest", "label": "Forest", "emoji": "🌿", "dots": ("#16a34a", "#f0fdf4", "#86efac")},
    {"id": "sunset", "label": "Sunset", "emoji": "🌅", "dots": ("#ea580c", "#fff7ed", "#fbbf24")},
    {"id": "candy", "label": "Candy", "emoji": "🍬", "dots": ("#db2777", "#fdf2f8", "#f9a8d4")},
    {"id": "night", "label": "Night", "emoji": "🌙", "dots": ("#a78bfa", "#0f172a", "#38bdf8")},
    {"id": "aura", "label": "Mystic", "emoji": "✨", "dots": ("#c084fc", "#fae8ff", "#67e8f9")},
    {"id": "rainbow", "label": "Rainbow", "emoji": "🌈", "dots": ("#ef4444", "#fbbf24", "#22c55e")},
    {"id": "beach", "label": "Beach", "emoji": "🏖️", "dots": ("#38bdf8", "#fde68a", "#fb923c")},
    {"id": "snow", "label": "Snow", "emoji": "❄️", "dots": ("#e0f2fe", "#94a3b8", "#38bdf8")},
    {"id": "meadow", "label": "Meadow", "emoji": "🌼", "dots": ("#84cc16", "#fef08a", "#4ade80")},
    {"id": "lemon", "label": "Sunshine", "emoji": "☀️", "dots": ("#facc15", "#fef9c3", "#fb923c")},
    {"id": "bubble", "label": "Bubbles", "emoji": "🫧", "dots": ("#67e8f9", "#e0f2fe", "#a78bfa")},
    {"id": "lava", "label": "Lava", "emoji": "🌋", "dots": ("#ef4444", "#fb923c", "#7f1d1d")},
    {"id": "galaxy", "label": "Galaxy", "emoji": "🌌", "dots": ("#4c1d95", "#22d3ee", "#f472b6")},
)


def is_valid_aura(aura: str | None) -> bool:
    return bool(aura) and str(aura).strip().lower() in AURA_IDS


def normalize_aura(aura: str | None) -> str | None:
    if not aura:
        return None
    a = str(aura).strip().lower()
    return a if a in AURA_IDS else None

# Lucky Spin wheel — order matches UI segments (clockwise from top)
SPIN_SEGMENTS = [
    {"id": "c10", "label": "10 🪙", "kind": "coins", "amount": 10, "weight": 22},
    {"id": "c25", "label": "25 🪙", "kind": "coins", "amount": 25, "weight": 18},
    {"id": "c5", "label": "5 🪙", "kind": "coins", "amount": 5, "weight": 20},
    {"id": "c50", "label": "50 🪙", "kind": "coins", "amount": 50, "weight": 12},
    {"id": "miss", "label": "Try again", "kind": "miss", "amount": 0, "weight": 10},
    {"id": "c100", "label": "100 🪙", "kind": "coins", "amount": 100, "weight": 8},
    {"id": "c15", "label": "15 🪙", "kind": "coins", "amount": 15, "weight": 14},
    {"id": "jackpot", "label": "JACKPOT!", "kind": "coins", "amount": 250, "weight": 3},
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_user_columns(conn):
    cols = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "coins" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN coins INTEGER NOT NULL DEFAULT 0")
    if "is_admin" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
    if "is_banned" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER NOT NULL DEFAULT 0")
    if "is_fake" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_fake INTEGER NOT NULL DEFAULT 0")
    if "god_mode" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN god_mode INTEGER NOT NULL DEFAULT 0")
    if "last_free_spin" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_free_spin TEXT")
    if "aura" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN aura TEXT")
    if "last_streak_bonus" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_streak_bonus TEXT")
    if "equipped_shirt" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN equipped_shirt TEXT")
    if "equipped_hat" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN equipped_hat TEXT")
    if "equipped_pants" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN equipped_pants TEXT")
    if "is_hacker" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_hacker INTEGER NOT NULL DEFAULT 0")
    if "is_developer" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_developer INTEGER NOT NULL DEFAULT 0")
    if "equipped_name" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN equipped_name TEXT")
    if "parent_email" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN parent_email TEXT")
    if "share_token" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN share_token TEXT")
    if "last_weekly_report_sent" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_weekly_report_sent TEXT")


def get_owner_admin_name() -> str:
    """Primary owner admin — cannot be demoted by other admins."""
    return os.environ.get("INITIAL_ADMIN_NAME", "Apex").strip()


def is_owner_admin_name(name: str) -> bool:
    owner = get_owner_admin_name()
    return bool(owner) and name.strip().lower() == owner.lower()


def _ensure_admin_user(conn):
    admin_name = get_owner_admin_name()
    if admin_name:
        conn.execute(
            "UPDATE users SET is_admin = 1 WHERE name = ? COLLATE NOCASE",
            (admin_name,),
        )


def _scores_sql(conn) -> str:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='scores'"
    ).fetchone()
    return (row["sql"] or "") if row else ""


def _needs_mode_migration(conn, mode_token: str) -> bool:
    sql = _scores_sql(conn)
    if not sql:
        return False
    return mode_token not in sql


def _migrate_modes_schema(conn):
    """Ensure scores/unlocks allow every mode in ALL_MODES."""
    sql = _scores_sql(conn)
    needed = (
        "'impossible'",
        "'top'",
        "'letters'",
        "'sounds'",
        "'beginner'",
    )
    needs_rebuild = bool(sql) and any(token not in sql for token in needed)
    if not needs_rebuild:
        for user in conn.execute("SELECT id FROM users").fetchall():
            for mode in ALL_MODES:
                conn.execute(
                    "INSERT OR IGNORE INTO scores (user_id, mode, points) VALUES (?, ?, 0)",
                    (user["id"], mode),
                )
        return

    conn.executescript(
        f"""
        CREATE TABLE scores_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mode TEXT NOT NULL CHECK (mode IN ({MODE_SQL_LIST})),
            points INTEGER NOT NULL DEFAULT 0,
            UNIQUE (user_id, mode),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        INSERT INTO scores_new (id, user_id, mode, points)
            SELECT id, user_id, mode, points FROM scores;
        DROP TABLE scores;
        ALTER TABLE scores_new RENAME TO scores;

        CREATE TABLE unlocks_new (
            user_id INTEGER NOT NULL,
            mode TEXT NOT NULL CHECK (mode IN ({UNLOCK_SQL_LIST})),
            unlocked_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (user_id, mode),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        INSERT INTO unlocks_new (user_id, mode, unlocked_at)
            SELECT user_id, mode, unlocked_at FROM unlocks;
        DROP TABLE unlocks;
        ALTER TABLE unlocks_new RENAME TO unlocks;
        """
    )
    for user in conn.execute("SELECT id FROM users").fetchall():
        for mode in ALL_MODES:
            conn.execute(
                "INSERT OR IGNORE INTO scores (user_id, mode, points) VALUES (?, ?, 0)",
                (user["id"], mode),
            )


def init_db():
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        conn.executescript(
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                coins INTEGER NOT NULL DEFAULT 0,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                mode TEXT NOT NULL CHECK (mode IN ({MODE_SQL_LIST})),
                points INTEGER NOT NULL DEFAULT 0,
                UNIQUE (user_id, mode),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS unlocks (
                user_id INTEGER NOT NULL,
                mode TEXT NOT NULL CHECK (mode IN ({UNLOCK_SQL_LIST})),
                unlocked_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (user_id, mode),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS activity (
                user_id INTEGER NOT NULL,
                day TEXT NOT NULL,
                correct INTEGER NOT NULL DEFAULT 0,
                attempts INTEGER NOT NULL DEFAULT 0,
                coins_earned INTEGER NOT NULL DEFAULT 0,
                UNIQUE (user_id, day),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                bought_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (user_id, item_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                price INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (seller_id, item_id),
                FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS play_sessions (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER NOT NULL DEFAULT 0,
                learned TEXT,
                mistakes TEXT,
                started TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        _ensure_user_columns(conn)
        _migrate_modes_schema(conn)
        _ensure_chat_table(conn)
        _ensure_review_table(conn)
        _ensure_likes_table(conn)
        _ensure_badge_tables(conn)
        _ensure_fluency_table(conn)
        _ensure_subscription_table(conn)
        _ensure_admin_user(conn)
        _ensure_starter_clothes(conn)
        conn.commit()
    finally:
        conn.close()


def get_play_session(user_id: int) -> dict | None:
    """Fetch current round data from DB."""
    import json
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT coins, learned, mistakes, started FROM play_sessions WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "user_id": user_id,
            "coins": int(row["coins"] or 0),
            "learned": json.loads(row["learned"] or "[]"),
            "mistakes": json.loads(row["mistakes"] or "[]"),
            "started": row["started"],
        }
    finally:
        conn.close()


def save_play_session(user_id: int, data: dict) -> None:
    """Save current round data to DB."""
    import json
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO play_sessions (user_id, coins, learned, mistakes, started)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                coins = excluded.coins,
                learned = excluded.learned,
                mistakes = excluded.mistakes,
                started = excluded.started
            """,
            (
                user_id,
                int(data.get("coins") or 0),
                json.dumps(data.get("learned") or []),
                json.dumps(data.get("mistakes") or []),
                data.get("started"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def clear_play_session(user_id: int) -> None:
    """Wipe round data."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM play_sessions WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def normalize_parent_email(raw: str | None) -> str | None:

    """Return a cleaned email, '' if empty, or None if invalid."""
    e = (raw or "").strip().lower()
    if not e:
        return ""
    if " " in e or "@" not in e or len(e) > 120:
        return None
    local, _, domain = e.partition("@")
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        return None
    return e


def get_parent_email(user_id: int) -> str:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT parent_email FROM users WHERE id = ?", (int(user_id),)
        ).fetchone()
        return (row["parent_email"] or "").strip() if row else ""
    finally:
        conn.close()


def set_parent_email(user_id: int, email: str | None) -> tuple[bool, str]:
    cleaned = normalize_parent_email(email)
    if cleaned is None:
        return False, "Please enter a real parent email, like mom@email.com."
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET parent_email = ? WHERE id = ?",
            (cleaned or None, int(user_id)),
        )
        conn.commit()
        return True, cleaned
    finally:
        conn.close()


def get_or_create_share_token(user_id: int) -> str:
    """Opaque id used by the public /share/<token> progress page — never the
    user's real id or name-based, so it can't be guessed or enumerated."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT share_token FROM users WHERE id = ?", (int(user_id),)
        ).fetchone()
        if row and row["share_token"]:
            return row["share_token"]
        token = secrets.token_urlsafe(16)
        conn.execute(
            "UPDATE users SET share_token = ? WHERE id = ?", (token, int(user_id))
        )
        conn.commit()
        return token
    finally:
        conn.close()


def get_user_by_share_token(token: str) -> dict | None:
    token = (token or "").strip()
    if not token:
        return None
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name FROM users WHERE share_token = ?", (token,)
        ).fetchone()
        return {"id": row["id"], "name": row["name"]} if row else None
    finally:
        conn.close()


def create_user(
    name: str,
    password: str,
    aura: str | None = None,
    parent_email: str | None = None,
) -> tuple[bool, str | int]:
    """Create user. Returns (ok, user_id or error message)."""
    name = name.strip()
    if not name:
        return False, "Please enter a name."
    if len(name) > 32:
        return False, "Name is too long."
    if not _NAME_ALLOWED_RE.match(name):
        return False, "Names can only have letters, numbers, spaces, and ' . -"
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters."
    aura_norm = normalize_aura(aura)
    if not aura_norm:
        return False, "Please choose your aura (theme)."
    email = normalize_parent_email(parent_email)
    if email is None:
        return False, "Please enter a real parent email, like mom@email.com."
    if not email:
        return False, "Ask a grown-up to type their email."

    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
        if existing:
            return False, "That name is already taken."

        cur = conn.execute(
            """
            INSERT INTO users (name, password_hash, coins, aura, parent_email)
            VALUES (?, ?, 0, ?, ?)
            """,
            (name, generate_password_hash(password), aura_norm, email),
        )
        user_id = cur.lastrowid
        for mode in ALL_MODES:
            conn.execute(
                "INSERT INTO scores (user_id, mode, points) VALUES (?, ?, 0)",
                (user_id, mode),
            )
        _grant_starter_clothes(conn, user_id)
        conn.commit()
        return True, user_id
    finally:
        conn.close()


def verify_user(name: str, password: str) -> tuple[bool, dict | str]:
    """Verify login. Returns (ok, user dict or error)."""
    name = name.strip()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id, name, password_hash, is_admin, is_banned, god_mode, aura, is_hacker
            FROM users WHERE name = ? COLLATE NOCASE
            """,
            (name,),
        ).fetchone()
        if not row or not check_password_hash(row["password_hash"], password):
            return False, "Wrong name or password."
        # banned column may be missing on very old rows — safe getattr via keys
        keys = row.keys()
        if "is_banned" in keys and row["is_banned"]:
            return False, "This account is banned."
        aura = None
        if "aura" in keys and row["aura"]:
            aura = normalize_aura(row["aura"])
        return True, {
            "id": row["id"],
            "name": row["name"],
            "is_admin": bool(row["is_admin"]),
            "god_mode": bool(row["god_mode"]) if "god_mode" in keys else False,
            "is_hacker": bool(row["is_hacker"]) if "is_hacker" in keys else False,
            "aura": aura,
        }
    finally:
        conn.close()


def get_user_aura(user_id: int) -> str | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT aura FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return None
        return normalize_aura(row["aura"])
    finally:
        conn.close()


def set_user_aura(user_id: int, aura: str) -> tuple[bool, str]:
    aura_norm = normalize_aura(aura)
    if not aura_norm:
        return False, "Pick a valid aura."
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "User not found."
        conn.execute(
            "UPDATE users SET aura = ? WHERE id = ?",
            (aura_norm, user_id),
        )
        conn.commit()
        return True, aura_norm
    finally:
        conn.close()


def _grant_starter_clothes(conn, user_id: int) -> None:
    for item_id in (DEFAULT_SHIRT, DEFAULT_HAT, DEFAULT_PANTS, DEFAULT_NAME):
        conn.execute(
            "INSERT OR IGNORE INTO inventory (user_id, item_id) VALUES (?, ?)",
            (user_id, item_id),
        )
    row = conn.execute(
        """
        SELECT equipped_shirt, equipped_hat, equipped_pants, equipped_name
        FROM users WHERE id = ?
        """,
        (user_id,),
    ).fetchone()
    shirt = (row["equipped_shirt"] if row else None) or DEFAULT_SHIRT
    hat = (row["equipped_hat"] if row else None) or DEFAULT_HAT
    pants = (row["equipped_pants"] if row else None) or DEFAULT_PANTS
    nam = (row["equipped_name"] if row else None) or DEFAULT_NAME
    if not get_item(shirt):
        shirt = DEFAULT_SHIRT
    if not get_item(hat):
        hat = DEFAULT_HAT
    if not get_item(pants):
        pants = DEFAULT_PANTS
    if not get_item(nam) or get_item(nam).get("slot") != "name":
        nam = DEFAULT_NAME
    conn.execute(
        """
        UPDATE users
        SET equipped_shirt = ?, equipped_hat = ?, equipped_pants = ?, equipped_name = ?
        WHERE id = ?
        """,
        (shirt, hat, pants, nam, user_id),
    )


def _ensure_starter_clothes(conn) -> None:
    for row in conn.execute("SELECT id FROM users").fetchall():
        _grant_starter_clothes(conn, row["id"])


def _owned_ids(conn, user_id: int) -> set[str]:
    rows = conn.execute(
        "SELECT item_id FROM inventory WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    return {r["item_id"] for r in rows}


def get_avatar(user_id: int) -> dict:
    """Equipped shirt, pants, accessory plus owned ids."""
    conn = get_connection()
    try:
        _grant_starter_clothes(conn, user_id)
        conn.commit()
        row = conn.execute(
            """
            SELECT coins, equipped_shirt, equipped_hat, equipped_pants, equipped_name
            FROM users WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
        shirt_item = get_item(DEFAULT_SHIRT)
        hat_item = get_item(DEFAULT_HAT)
        pants_item = get_item(DEFAULT_PANTS)
        name_item = get_item(DEFAULT_NAME)
        coins = 0
        owned = [DEFAULT_SHIRT, DEFAULT_HAT, DEFAULT_PANTS, DEFAULT_NAME]
        if row:
            shirt_item = get_item(row["equipped_shirt"]) or shirt_item
            hat_item = get_item(row["equipped_hat"]) or hat_item
            pants_item = get_item(row["equipped_pants"]) or pants_item
            name_item = get_item(row["equipped_name"]) or name_item
            if not name_item or name_item.get("slot") != "name":
                name_item = get_item(DEFAULT_NAME)
            owned = sorted(_owned_ids(conn, user_id))
            coins = int(row["coins"] or 0)
        shirt = item_public(shirt_item)
        hat = item_public(hat_item)
        pants = item_public(pants_item)
        nam = item_public(name_item)
        return {
            "shirt": shirt,
            "hat": hat,
            "pants": pants,
            "name": nam,
            "name_style": nam.get("anim") or "plain",
            "owned": owned,
            "coins": coins,
            "admin_aura": bool(shirt.get("aura") or hat.get("aura") or pants.get("aura")),
        }
    finally:
        conn.close()


def _catalog_slot(items, owned, equipped_id, admin_owners, user_id):
    out = []
    for item in items:
        pub = item_public(item)
        pub["owned"] = item["id"] in owned
        pub["equipped"] = item["id"] == equipped_id
        if item.get("admin_set"):
            limit = int(item.get("owner_limit") or ADMIN_OWNER_LIMIT)
            pub["owner_count"] = len(admin_owners)
            pub["owner_limit"] = limit
            pub["slots_left"] = max(0, limit - len(admin_owners))
            in_club = user_id in admin_owners
            pub["can_buy"] = pub["owned"] or in_club or len(admin_owners) < limit
        else:
            pub["can_buy"] = True
        out.append(pub)
    return out


def _admin_owner_ids(conn) -> set[int]:
    placeholders = ",".join("?" * len(ADMIN_ITEM_IDS))
    rows = conn.execute(
        f"SELECT DISTINCT user_id FROM inventory WHERE item_id IN ({placeholders})",
        ADMIN_ITEM_IDS,
    ).fetchall()
    return {int(r["user_id"]) for r in rows}


def _dev_owner_ids(conn) -> set[int]:
    placeholders = ",".join("?" * len(DEV_ITEM_IDS))
    rows = conn.execute(
        f"SELECT DISTINCT user_id FROM inventory WHERE item_id IN ({placeholders})",
        DEV_ITEM_IDS,
    ).fetchall()
    return {int(r["user_id"]) for r in rows}


def get_shop_catalog(user_id: int) -> dict:
    avatar = get_avatar(user_id)
    owned = set(avatar["owned"])
    conn = get_connection()
    try:
        admin_owners = _admin_owner_ids(conn)
    finally:
        conn.close()
    shirts = _catalog_slot(
        items_for_slot("shirt"), owned, avatar["shirt"]["id"], admin_owners, user_id
    )
    pants = _catalog_slot(
        items_for_slot("pants"), owned, avatar["pants"]["id"], admin_owners, user_id
    )
    hats = _catalog_slot(
        items_for_slot("hat"), owned, avatar["hat"]["id"], admin_owners, user_id
    )
    names = _catalog_slot(
        items_for_slot("name"), owned, avatar["name"]["id"], admin_owners, user_id
    )
    return {
        "avatar": avatar,
        "shirts": shirts,
        "pants": pants,
        "hats": hats,
        "names": names,
        "coins": avatar["coins"],
        "admin_owners": len(admin_owners),
        "admin_limit": ADMIN_OWNER_LIMIT,
    }


def buy_shop_item(user_id: int, item_id: str) -> tuple[bool, str | dict]:
    item = get_item(item_id)
    if not item:
        return False, "That item is not in the shop."
    cost = int(item["cost"])
    slot_col = slot_column(item["slot"])
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        _grant_starter_clothes(conn, user_id)
        owned = _owned_ids(conn, user_id)
        if item["id"] in owned:
            conn.rollback()
            return False, "You already have that!"

        if item.get("admin_set"):
            owners = _admin_owner_ids(conn)
            if user_id not in owners and len(owners) >= ADMIN_OWNER_LIMIT:
                conn.rollback()
                return False, "Only 2 players in the whole game can buy Admin gear."

        if item.get("dev_set"):
            owners = _dev_owner_ids(conn)
            if user_id not in owners and len(owners) >= DEV_OWNER_LIMIT:
                conn.rollback()
                return False, "Only 1 player in the whole game can buy Developer gear."

        if cost > 0 and not is_user_god(user_id):
            row = conn.execute(
                "SELECT coins FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            coins = int(row["coins"]) if row else 0
            if coins < cost:
                conn.rollback()
                return False, f"Need {cost} coins (you have {coins})."
            conn.execute(
                "UPDATE users SET coins = coins - ? WHERE id = ?",
                (cost, user_id),
            )
            owner_id = _owner_user_id(conn)
            if owner_id and owner_id != user_id:
                conn.execute(
                    "UPDATE users SET coins = coins + ? WHERE id = ?",
                    (cost, owner_id),
                )

        conn.execute(
            "INSERT OR IGNORE INTO inventory (user_id, item_id) VALUES (?, ?)",
            (user_id, item["id"]),
        )
        conn.execute(
            f"UPDATE users SET {slot_col} = ? WHERE id = ?",
            (item["id"], user_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    catalog = get_shop_catalog(user_id)
    return True, {
        "message": f"You bought {item['label']}!",
        "catalog": catalog,
    }


def equip_shop_item(user_id: int, item_id: str) -> tuple[bool, str | dict]:
    item = get_item(item_id)
    if not item:
        return False, "Unknown item."
    conn = get_connection()
    try:
        _grant_starter_clothes(conn, user_id)
        owned = _owned_ids(conn, user_id)
        if item["id"] not in owned:
            conn.commit()
            return False, "Buy it first!"
        slot_col = slot_column(item["slot"])
        conn.execute(
            f"UPDATE users SET {slot_col} = ? WHERE id = ?",
            (item["id"], user_id),
        )
        conn.commit()
    finally:
        conn.close()
    return True, {
        "message": (
            f"Using {item['label']}!"
            if item["slot"] == "name"
            else f"Wearing {item['label']}!"
        ),
        "catalog": get_shop_catalog(user_id),
    }


STARTER_ITEM_IDS = frozenset(
    {DEFAULT_SHIRT, DEFAULT_HAT, DEFAULT_PANTS, DEFAULT_NAME}
)
MAX_LISTING_PRICE = 1_000_000_000_000_000


def _owner_user_id(conn) -> int | None:
    name = get_owner_admin_name()
    if not name:
        return None
    row = conn.execute(
        "SELECT id FROM users WHERE name = ? COLLATE NOCASE",
        (name,),
    ).fetchone()
    return int(row["id"]) if row else None


def _unequip_item(conn, user_id: int, item_id: str) -> None:
    item = get_item(item_id)
    if not item:
        return
    col = slot_column(item["slot"])
    row = conn.execute(
        f"SELECT {col} FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if not row or row[col] != item_id:
        return
    fallback = {
        "shirt": DEFAULT_SHIRT,
        "pants": DEFAULT_PANTS,
        "hat": DEFAULT_HAT,
        "name": DEFAULT_NAME,
    }.get(item["slot"], DEFAULT_HAT)
    conn.execute(
        f"UPDATE users SET {col} = ? WHERE id = ?",
        (fallback, user_id),
    )


def _listing_row(conn, listing_id: int, viewer_id: int) -> dict | None:
    row = conn.execute(
        """
        SELECT l.id, l.seller_id, l.item_id, l.price, l.created_at,
               u.name AS seller_name, u.equipped_name AS seller_name_item
        FROM listings l
        JOIN users u ON u.id = l.seller_id
        WHERE l.id = ?
        """,
        (listing_id,),
    ).fetchone()
    if not row:
        return None
    item = get_item(row["item_id"])
    if not item:
        return None
    pub = item_public(item)
    return {
        "id": row["id"],
        "seller_id": row["seller_id"],
        "seller_name": row["seller_name"],
        "seller_name_style": name_style(row["seller_name_item"]),
        "item_id": row["item_id"],
        "price": int(row["price"]),
        "price_label": cost_label(int(row["price"])),
        "item": pub,
        "is_mine": row["seller_id"] == viewer_id,
    }


def get_player_market(user_id: int) -> dict:
    avatar = get_avatar(user_id)
    owned = set(avatar["owned"])
    conn = get_connection()
    try:
        listed_rows = conn.execute(
            "SELECT item_id FROM listings WHERE seller_id = ?",
            (user_id,),
        ).fetchall()
        listed = {r["item_id"] for r in listed_rows}
        market_rows = conn.execute(
            """
            SELECT l.id, l.seller_id, l.item_id, l.price, u.name AS seller_name,
                   u.equipped_name AS seller_name_item
            FROM listings l
            JOIN users u ON u.id = l.seller_id
            ORDER BY l.created_at DESC
            """
        ).fetchall()
    finally:
        conn.close()

    listings = []
    for row in market_rows:
        item = get_item(row["item_id"])
        if not item:
            continue
        listings.append(
            {
                "id": row["id"],
                "seller_id": row["seller_id"],
                "seller_name": row["seller_name"],
                "seller_name_style": name_style(row["seller_name_item"]),
                "item_id": row["item_id"],
                "price": int(row["price"]),
                "price_label": cost_label(int(row["price"])),
                "item": item_public(item),
                "is_mine": row["seller_id"] == user_id,
            }
        )

    sellable = []
    for item_id in owned:
        item = get_item(item_id)
        if not item:
            continue
        if item_id in STARTER_ITEM_IDS or item.get("admin_set") or item.get("dev_set"):
            continue
        pub = item_public(item)
        pub["listed"] = item_id in listed
        pub["equipped"] = item_id in (
            avatar["shirt"]["id"],
            avatar["pants"]["id"],
            avatar["hat"]["id"],
            avatar["name"]["id"],
        )
        sellable.append(pub)

    return {
        "listings": listings,
        "sellable": sellable,
        "coins": avatar["coins"],
    }


def list_item_for_sale(
    user_id: int, item_id: str, price: int
) -> tuple[bool, str | dict]:
    item = get_item(item_id)
    if not item:
        return False, "Unknown item."
    if item_id in STARTER_ITEM_IDS:
        return False, "Starter items cannot be sold."
    if item.get("admin_set"):
        return False, "Admin gear cannot be sold."
    if item.get("dev_set"):
        return False, "Developer gear cannot be sold."
    try:
        price = int(price)
    except (TypeError, ValueError):
        return False, "Enter a coin price."
    if price < 1 or price > MAX_LISTING_PRICE:
        return False, "Price must be from 1 to 1Q coins."

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        owned = _owned_ids(conn, user_id)
        if item_id not in owned:
            conn.rollback()
            return False, "You do not own that."
        exists = conn.execute(
            "SELECT id FROM listings WHERE seller_id = ? AND item_id = ?",
            (user_id, item_id),
        ).fetchone()
        if exists:
            conn.rollback()
            return False, "Already listed."
        conn.execute(
            "INSERT INTO listings (seller_id, item_id, price) VALUES (?, ?, ?)",
            (user_id, item_id, price),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return True, {
        "message": f"Listed {item['label']} for 🪙 {cost_label(price)}.",
        "market": get_player_market(user_id),
        "catalog": get_shop_catalog(user_id),
    }


def unlist_item(user_id: int, listing_id: int) -> tuple[bool, str | dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, seller_id FROM listings WHERE id = ?",
            (listing_id,),
        ).fetchone()
        if not row:
            return False, "Listing gone."
        if row["seller_id"] != user_id:
            return False, "That is not your listing."
        conn.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
        conn.commit()
    finally:
        conn.close()
    return True, {
        "message": "Listing taken down.",
        "market": get_player_market(user_id),
        "catalog": get_shop_catalog(user_id),
    }


def buy_player_listing(buyer_id: int, listing_id: int) -> tuple[bool, str | dict]:
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            """
            SELECT id, seller_id, item_id, price
            FROM listings WHERE id = ?
            """,
            (listing_id,),
        ).fetchone()
        if not row:
            conn.rollback()
            return False, "That sale already ended."
        seller_id = int(row["seller_id"])
        item_id = row["item_id"]
        price = int(row["price"])
        if seller_id == buyer_id:
            conn.rollback()
            return False, "You cannot buy your own listing."
        item = get_item(item_id)
        if not item:
            conn.rollback()
            return False, "Unknown item."

        buyer_owned = _owned_ids(conn, buyer_id)
        if item_id in buyer_owned:
            conn.rollback()
            return False, "You already have that!"

        seller_owned = _owned_ids(conn, seller_id)
        if item_id not in seller_owned:
            conn.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
            conn.commit()
            return False, "Seller no longer has that item."

        if not is_user_god(buyer_id):
            brow = conn.execute(
                "SELECT coins FROM users WHERE id = ?", (buyer_id,)
            ).fetchone()
            coins = int(brow["coins"]) if brow else 0
            if coins < price:
                conn.rollback()
                return False, f"Need {price} coins (you have {coins})."
            conn.execute(
                "UPDATE users SET coins = coins - ? WHERE id = ?",
                (price, buyer_id),
            )
        conn.execute(
            "UPDATE users SET coins = coins + ? WHERE id = ?",
            (price, seller_id),
        )
        _unequip_item(conn, seller_id, item_id)
        conn.execute(
            "DELETE FROM inventory WHERE user_id = ? AND item_id = ?",
            (seller_id, item_id),
        )
        conn.execute(
            "INSERT OR IGNORE INTO inventory (user_id, item_id) VALUES (?, ?)",
            (buyer_id, item_id),
        )
        slot_col = slot_column(item["slot"])
        conn.execute(
            f"UPDATE users SET {slot_col} = ? WHERE id = ?",
            (item_id, buyer_id),
        )
        conn.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return True, {
        "message": f"Bought {item['label']} for 🪙 {cost_label(price)}. Coins went to the seller!",
        "market": get_player_market(buyer_id),
        "catalog": get_shop_catalog(buyer_id),
    }


def get_user_scores(user_id: int) -> dict[str, int]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT mode, points FROM scores WHERE user_id = ?", (user_id,)
        ).fetchall()
        scores = {mode: 0 for mode in ALL_MODES}
        for row in rows:
            scores[row["mode"]] = row["points"]
        return scores
    finally:
        conn.close()


def get_user_coins(user_id: int) -> int:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT coins FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return int(row["coins"]) if row else 0
    finally:
        conn.close()


def get_unlocked_modes(user_id: int) -> set[str]:
    unlocked = set(FREE_MODES)
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT mode FROM unlocks WHERE user_id = ?", (user_id,)
        ).fetchall()
        for row in rows:
            unlocked.add(row["mode"])
        return unlocked
    finally:
        conn.close()


def get_user_wallet(user_id: int) -> dict:
    unlocked = get_unlocked_modes(user_id)
    if is_user_god(user_id):
        unlocked = set(ALL_MODES)
    return {
        "coins": get_user_coins(user_id),
        "unlocked": {mode: mode in unlocked for mode in ALL_MODES},
    }


def is_mode_unlocked(user_id: int, mode: str) -> bool:
    if mode in FREE_MODES:
        return True
    if is_user_god(user_id):
        return True
    if is_subscribed(user_id):
        # A paid subscription unlocks every mode instantly — it doesn't replace
        # the coin-unlock economy, it's an alternative path for parents who'd
        # rather not wait for their kid to grind coins.
        return True
    return mode in get_unlocked_modes(user_id)


def _today() -> str:
    from datetime import date

    return date.today().isoformat()


def log_activity(
    user_id: int,
    *,
    correct: int = 0,
    attempts: int = 0,
    coins_earned: int = 0,
) -> None:
    """Record daily practice stats (correct answers, attempts, coins)."""
    day = _today()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO activity (user_id, day, correct, attempts, coins_earned)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, day) DO UPDATE SET
                correct = correct + excluded.correct,
                attempts = attempts + excluded.attempts,
                coins_earned = coins_earned + excluded.coins_earned
            """,
            (user_id, day, correct, attempts, coins_earned),
        )
        conn.commit()
    finally:
        conn.close()


def get_user_progress(user_id: int) -> dict:
    """Today's stats + consecutive-day play streak."""
    from datetime import date, timedelta

    day = _today()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT correct, attempts, coins_earned FROM activity
            WHERE user_id = ? AND day = ?
            """,
            (user_id, day),
        ).fetchone()
        today = {
            "correct": int(row["correct"]) if row else 0,
            "attempts": int(row["attempts"]) if row else 0,
            "coins_earned": int(row["coins_earned"]) if row else 0,
        }

        days = {
            r["day"]
            for r in conn.execute(
                "SELECT day FROM activity WHERE user_id = ? AND (correct > 0 OR attempts > 0)",
                (user_id,),
            ).fetchall()
        }
        streak = 0
        cursor = date.today()
        # If no play today, streak can still count from yesterday
        if day not in days:
            cursor = cursor - timedelta(days=1)
        while cursor.isoformat() in days:
            streak += 1
            cursor = cursor - timedelta(days=1)

        week_rows = conn.execute(
            """
            SELECT COALESCE(SUM(correct), 0) AS c,
                   COALESCE(SUM(coins_earned), 0) AS coins
            FROM activity
            WHERE user_id = ? AND day >= date('now', '-6 days')
            """,
            (user_id,),
        ).fetchone()

        return {
            "today": today,
            "streak": streak,
            "week_correct": int(week_rows["c"]) if week_rows else 0,
            "week_coins": int(week_rows["coins"]) if week_rows else 0,
        }
    finally:
        conn.close()


def get_progress_summary(user_id: int) -> dict:
    """Parent-facing progress snapshot: words learned, speaking progress, streak.

    Distinct from get_user_progress() (today/streak/week activity counts) — this
    adds the "proof of learning" numbers parents actually want to see and share:
    total distinct words ever learned, new words learned in the last 7 days
    (using review_words.first_at, not last_at, so repeated reviews don't inflate
    "new this week"), and how many Family spoken-English phrases are mastered.
    """
    import words as _words

    conn = get_connection()
    try:
        total_row = conn.execute(
            """
            SELECT COUNT(DISTINCT word) AS c FROM review_words
            WHERE user_id = ? AND mode != ?
            """,
            (int(user_id), FLUENCY_MODE),
        ).fetchone()
        week_row = conn.execute(
            """
            SELECT COUNT(DISTINCT word) AS c FROM review_words
            WHERE user_id = ? AND mode != ? AND first_at >= date('now', '-6 days')
            """,
            (int(user_id), FLUENCY_MODE),
        ).fetchone()
        practice_days_row = conn.execute(
            """
            SELECT COUNT(DISTINCT day) AS c FROM activity
            WHERE user_id = ? AND correct > 0 AND day >= date('now', '-6 days')
            """,
            (int(user_id),),
        ).fetchone()
    finally:
        conn.close()

    progress = get_user_progress(user_id)
    family_total = len(_words.IMPOSSIBLE_PHRASES)
    return {
        "total_words": int(total_row["c"] or 0) if total_row else 0,
        "words_this_week": int(week_row["c"] or 0) if week_row else 0,
        "practice_days_this_week": int(practice_days_row["c"] or 0) if practice_days_row else 0,
        "family_mastered": count_family_mastered(user_id),
        "family_total": family_total,
        "streak": progress["streak"],
        "week_correct": progress["week_correct"],
        "today_correct": progress["today"]["correct"],
    }


def get_newly_learned_words(user_id: int, days: int = 7, limit: int = 20) -> list[str]:
    """Words first answered correctly in the last N days — for the weekly email."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT word FROM review_words
            WHERE user_id = ? AND mode != ? AND first_at >= date('now', ?)
            ORDER BY first_at DESC
            LIMIT ?
            """,
            (int(user_id), FLUENCY_MODE, f"-{int(days)} days", int(limit)),
        ).fetchall()
        return [str(r["word"]) for r in rows]
    finally:
        conn.close()


def get_newly_mastered_phrases(user_id: int, days: int = 7, limit: int = 6) -> list[str]:
    """Family spoken-English phrases first answered correctly in the last N days."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT word FROM review_words
            WHERE user_id = ? AND mode = ? AND first_at >= date('now', ?)
            ORDER BY first_at DESC
            LIMIT ?
            """,
            (int(user_id), FLUENCY_MODE, f"-{int(days)} days", int(limit)),
        ).fetchall()
        return [str(r["word"]) for r in rows]
    finally:
        conn.close()


def get_users_due_weekly_report() -> list[dict]:
    """Everyone with a parent email who: has played in the last 14 days (so we
    don't email parents of abandoned accounts) and hasn't already gotten a
    report in the last 6 days (so re-running the send task is safe/idempotent).
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT u.id, u.name, u.parent_email
            FROM users u
            WHERE u.parent_email IS NOT NULL AND u.parent_email != ''
              AND (u.last_weekly_report_sent IS NULL
                   OR u.last_weekly_report_sent <= date('now', '-6 days'))
              AND EXISTS (
                  SELECT 1 FROM activity a
                  WHERE a.user_id = u.id AND a.day >= date('now', '-14 days')
                    AND (a.correct > 0 OR a.attempts > 0)
              )
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def mark_weekly_report_sent(user_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET last_weekly_report_sent = date('now') WHERE id = ?",
            (int(user_id),),
        )
        conn.commit()
    finally:
        conn.close()


def _streak_bonus_amount(streak: int) -> int:
    if streak in STREAK_BONUSES:
        return STREAK_BONUSES[streak]
    if streak >= 14 and streak % 7 == 0:
        return STREAK_BONUSES[7]
    return 0


def claim_streak_bonus(user_id: int) -> dict:
    """Grant a once-a-day coin treat on streak milestones (1 / 3 / 7 / every 7 after)."""
    progress = get_user_progress(user_id)
    streak = int(progress.get("streak") or 0)
    amount = _streak_bonus_amount(streak)
    empty = {
        "granted": False,
        "amount": 0,
        "streak": streak,
        "coins": get_user_coins(user_id),
    }
    if amount < 1:
        return empty

    day = _today()
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT coins, last_streak_bonus FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            conn.rollback()
            return empty
        if row["last_streak_bonus"] == day:
            conn.rollback()
            return {**empty, "coins": int(row["coins"])}
        coins = int(row["coins"]) + amount
        conn.execute(
            "UPDATE users SET coins = ?, last_streak_bonus = ? WHERE id = ?",
            (coins, day, user_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    log_activity(user_id, coins_earned=amount)
    return {
        "granted": True,
        "amount": amount,
        "streak": streak,
        "coins": coins,
    }


def get_all_users_progress() -> list[dict]:
    """Progress snapshot for admin panel."""
    users = get_all_users()
    conn = get_connection()
    try:
        subscribed_ids = {
            int(r["user_id"])
            for r in conn.execute(
                "SELECT user_id FROM subscriptions WHERE is_active = 1 AND end_date >= date('now')"
            ).fetchall()
        }
    finally:
        conn.close()
    out = []
    for u in users:
        prog = get_user_progress(u["id"])
        out.append({**u, "progress": prog, "is_subscribed": u["id"] in subscribed_ids})
    return out


def add_points(user_id: int, mode: str, points: int) -> int:
    """Add leaderboard points for a mode; returns new total."""
    if mode not in ALL_MODES:
        raise ValueError("Invalid mode")
    if points < 0:
        raise ValueError("Points must be non-negative")

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO scores (user_id, mode, points) VALUES (?, ?, ?)
            ON CONFLICT(user_id, mode) DO UPDATE SET points = points + excluded.points
            """,
            (user_id, mode, points),
        )
        conn.commit()
        row = conn.execute(
            "SELECT points FROM scores WHERE user_id = ? AND mode = ?",
            (user_id, mode),
        ).fetchone()
        total = int(row["points"]) if row else points
    finally:
        conn.close()

    # Count as one correct answer for daily progress
    log_activity(user_id, correct=1, attempts=1, coins_earned=points)
    return total


def add_coins(user_id: int, amount: int) -> int:
    """Add coins to wallet; returns new balance."""
    if amount < 0:
        raise ValueError("Amount must be non-negative")

    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET coins = coins + ? WHERE id = ?",
            (amount, user_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT coins FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return int(row["coins"]) if row else amount
    finally:
        conn.close()


def unlock_mode(user_id: int, mode: str) -> tuple[bool, str | dict]:
    """Spend coins to unlock a mode. Returns (ok, wallet dict or error)."""
    if mode in FREE_MODES:
        return False, "That mode is already free."
    if mode not in UNLOCK_COSTS:
        return False, "Unknown mode."

    cost = UNLOCK_COSTS[mode]
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute(
            "SELECT 1 FROM unlocks WHERE user_id = ? AND mode = ?",
            (user_id, mode),
        ).fetchone():
            conn.rollback()
            return False, "Already unlocked."

        row = conn.execute(
            "SELECT coins FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            return False, "User not found."

        coins = int(row["coins"])
        if coins < cost:
            conn.rollback()
            return False, f"Need {cost} coins — you have {coins}."

        conn.execute(
            "UPDATE users SET coins = coins - ? WHERE id = ?",
            (cost, user_id),
        )
        conn.execute(
            "INSERT INTO unlocks (user_id, mode) VALUES (?, ?)",
            (user_id, mode),
        )
        conn.commit()
        return True, get_user_wallet(user_id)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def is_user_admin(user_id: int) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT is_admin FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return bool(row and row["is_admin"])
    finally:
        conn.close()


def get_all_users() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT u.id, u.name, u.coins, u.is_admin, u.created_at,
                   COALESCE(u.is_banned, 0) AS is_banned,
                   COALESCE(u.is_fake, 0) AS is_fake,
                   COALESCE(u.god_mode, 0) AS god_mode,
                   COALESCE(u.is_hacker, 0) AS is_hacker,
                   COALESCE(u.is_developer, 0) AS is_developer
            FROM users u
            ORDER BY u.id ASC
            """
        ).fetchall()
        score_map: dict[int, dict[str, int]] = {}
        for srow in conn.execute(
            "SELECT user_id, mode, points FROM scores"
        ).fetchall():
            score_map.setdefault(int(srow["user_id"]), {})[srow["mode"]] = int(
                srow["points"] or 0
            )
        users = []
        for row in rows:
            unlocks = conn.execute(
                "SELECT mode FROM unlocks WHERE user_id = ?", (row["id"],)
            ).fetchall()
            unlocked = list(FREE_MODES) + [u["mode"] for u in unlocks]
            admin_owned = conn.execute(
                f"""
                SELECT item_id FROM inventory
                WHERE user_id = ? AND item_id IN ({",".join("?" * len(ADMIN_ITEM_IDS))})
                """,
                (row["id"], *ADMIN_ITEM_IDS),
            ).fetchall()
            dev_owned = conn.execute(
                f"""
                SELECT item_id FROM inventory
                WHERE user_id = ? AND item_id IN ({",".join("?" * len(DEV_ITEM_IDS))})
                """,
                (row["id"], *DEV_ITEM_IDS),
            ).fetchall()
            users.append({
                "id": row["id"],
                "name": row["name"],
                "coins": row["coins"],
                "is_admin": bool(row["is_admin"]),
                "is_owner": is_owner_admin_name(row["name"]),
                "is_banned": bool(row["is_banned"]),
                "is_fake": bool(row["is_fake"]),
                "god_mode": bool(row["god_mode"]),
                "is_hacker": bool(row["is_hacker"]) or is_owner_admin_name(row["name"]),
                "has_admin_gear": bool(admin_owned),
                "is_developer": bool(row["is_developer"]),
                "has_dev_gear": bool(dev_owned),
                "created_at": row["created_at"],
                "scores": {
                    mode: int(score_map.get(int(row["id"]), {}).get(mode, 0) or 0)
                    for mode in ALL_MODES
                },
                "unlocked": unlocked,
            })
        return users
    finally:
        conn.close()


def count_admins() -> int:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT COUNT(*) AS n FROM users WHERE is_admin = 1"
        ).fetchone()["n"]
    finally:
        conn.close()


def get_admin_users() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, name, created_at
            FROM users
            WHERE is_admin = 1
            ORDER BY id ASC
            """
        ).fetchall()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "created_at": r["created_at"],
                "is_owner": is_owner_admin_name(r["name"]),
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_admin_stats() -> dict:
    conn = get_connection()
    try:
        total_users = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        total_coins = conn.execute(
            "SELECT COALESCE(SUM(coins), 0) AS n FROM users"
        ).fetchone()["n"]
        total_unlocks = conn.execute("SELECT COUNT(*) AS n FROM unlocks").fetchone()["n"]
        total_admins = conn.execute(
            "SELECT COUNT(*) AS n FROM users WHERE is_admin = 1"
        ).fetchone()["n"]
        return {
            "total_users": total_users,
            "total_coins": total_coins,
            "total_unlocks": total_unlocks,
            "total_admins": total_admins,
        }
    finally:
        conn.close()


def admin_set_admin_role(
    user_id: int, is_admin: bool, actor_id: int
) -> tuple[bool, str | dict]:
    """Promote or demote a player's admin access."""
    conn = get_connection()
    try:
        target = conn.execute(
            "SELECT id, name, is_admin FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not target:
            return False, "User not found."

        actor = conn.execute(
            "SELECT id, name, is_admin FROM users WHERE id = ?", (actor_id,)
        ).fetchone()
        if not actor or not actor["is_admin"]:
            return False, "Only admins can change roles."

        if user_id == actor_id and not is_admin:
            return False, "You cannot remove your own admin access."

        # Owner (INITIAL_ADMIN_NAME) cannot be demoted by anyone.
        if target["is_admin"] and not is_admin and is_owner_admin_name(target["name"]):
            return False, "Cannot remove admin from the owner account."

        # Only the owner can promote/demote other admins.
        # Secondary admins cannot remove or grant admin power.
        if not is_owner_admin_name(actor["name"]):
            return False, "Only the owner can add or remove admins."

        if target["is_admin"] and not is_admin and count_admins() <= 1:
            return False, "Cannot remove the last admin."

        conn.execute(
            "UPDATE users SET is_admin = ? WHERE id = ?",
            (1 if is_admin else 0, user_id),
        )
        conn.commit()
        return True, {
            "id": target["id"],
            "name": target["name"],
            "is_admin": is_admin,
        }
    finally:
        conn.close()


def admin_set_coins(user_id: int, coins: int, actor_id: int) -> tuple[bool, str | int]:
    if coins < 0:
        return False, "Coins cannot be negative."
    conn = get_connection()
    try:
        row = conn.execute("SELECT id, name FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "User not found."

        # Only the owner can change the owner's own coin balance.
        if is_owner_admin_name(row["name"]):
            actor = conn.execute(
                "SELECT name FROM users WHERE id = ?", (actor_id,)
            ).fetchone()
            if not actor or not is_owner_admin_name(actor["name"]):
                return False, "Only the owner can change the owner's coins."

        conn.execute("UPDATE users SET coins = ? WHERE id = ?", (coins, user_id))
        conn.commit()
        return True, coins
    finally:
        conn.close()


def admin_grant_unlock(user_id: int, mode: str) -> tuple[bool, str]:
    if mode in FREE_MODES:
        return False, "That mode is already free."
    if mode not in UNLOCK_COSTS:
        return False, "Invalid mode."
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "User not found."
        conn.execute(
            "INSERT OR IGNORE INTO unlocks (user_id, mode) VALUES (?, ?)",
            (user_id, mode),
        )
        conn.commit()
        return True, "Unlocked."
    finally:
        conn.close()


def admin_revoke_unlock(user_id: int, mode: str) -> tuple[bool, str]:
    """Lock a paid mode for a player (Normal / Hard / Top). Easy cannot be locked."""
    if mode in FREE_MODES:
        return False, "Starter modes are free and cannot be locked."
    if mode not in UNLOCK_COSTS:
        return False, "Invalid mode."
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "User not found."
        cur = conn.execute(
            "DELETE FROM unlocks WHERE user_id = ? AND mode = ?",
            (user_id, mode),
        )
        conn.commit()
        if cur.rowcount == 0:
            return False, f"{mode.title()} was already locked."
        return True, f"{mode.title()} locked."
    finally:
        conn.close()


def admin_lock_all_paid_modes(user_id: int) -> tuple[bool, str]:
    """Lock Normal, Hard, Top, Impossible for a player. Easy stays free."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "User not found."
        placeholders = ",".join("?" * len(LOCKED_MODES))
        conn.execute(
            f"DELETE FROM unlocks WHERE user_id = ? AND mode IN ({placeholders})",
            (user_id, *LOCKED_MODES),
        )
        conn.commit()
        return True, "Paid modes locked (Normal–Family)."
    finally:
        conn.close()


def admin_reset_scores(user_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "User not found."
        conn.execute(
            "UPDATE scores SET points = 0 WHERE user_id = ?", (user_id,)
        )
        conn.commit()
        return True, "Scores reset."
    finally:
        conn.close()


def admin_set_password(user_id: int, new_password: str, actor_id: int) -> tuple[bool, str]:
    """Admin sets a new password for a player."""
    if not new_password or len(new_password) < 6:
        return False, "Password must be at least 6 characters."
    conn = get_connection()
    try:
        row = conn.execute("SELECT id, name FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "User not found."

        # Only the owner can reset the owner's own password — otherwise a secondary
        # admin could take over the owner account and self-promote via admin_set_admin_role.
        if is_owner_admin_name(row["name"]):
            actor = conn.execute(
                "SELECT name FROM users WHERE id = ?", (actor_id,)
            ).fetchone()
            if not actor or not is_owner_admin_name(actor["name"]):
                return False, "Only the owner can reset the owner's password."

        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (generate_password_hash(new_password), user_id),
        )
        conn.commit()
        return True, f"Password updated for {row['name']}."
    finally:
        conn.close()


def spend_coins(user_id: int, amount: int) -> tuple[bool, str | int]:
    """Spend coins; returns (ok, new balance or error)."""
    if amount < 1:
        return False, "Invalid amount."
    # God Mode: free hints / free spends
    if is_user_god(user_id):
        return True, get_user_coins(user_id)
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT coins FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            return False, "User not found."
        coins = int(row["coins"])
        if coins < amount:
            conn.rollback()
            return False, f"Need {amount} coins (you have {coins})."
        conn.execute(
            "UPDATE users SET coins = coins - ? WHERE id = ?",
            (amount, user_id),
        )
        conn.commit()
        return True, coins - amount
    finally:
        conn.close()


def admin_delete_user(user_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, is_admin FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return False, "User not found."
        if row["is_admin"]:
            return False, "Cannot delete an admin account."
        conn.execute("DELETE FROM listings WHERE seller_id = ?", (user_id,))
        conn.execute("DELETE FROM inventory WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True, "User deleted."
    finally:
        conn.close()


def is_user_god(user_id: int) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT god_mode FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return bool(row and row["god_mode"])
    finally:
        conn.close()


def set_god_mode(user_id: int, enabled: bool) -> tuple[bool, str]:
    """Owner-only god mode flag. Callers must enforce owner check."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return False, "User not found."
        if not is_owner_admin_name(row["name"]):
            return False, "God Mode is only for Apex Shade (owner)."
        conn.execute(
            "UPDATE users SET god_mode = ? WHERE id = ?",
            (1 if enabled else 0, user_id),
        )
        if enabled:
            # Max coins + all unlocks while enabling
            conn.execute(
                "UPDATE users SET coins = MAX(coins, 999999) WHERE id = ?",
                (user_id,),
            )
            for mode in LOCKED_MODES:
                conn.execute(
                    "INSERT OR IGNORE INTO unlocks (user_id, mode) VALUES (?, ?)",
                    (user_id, mode),
                )
        conn.commit()
        return True, "God Mode ON." if enabled else "God Mode OFF."
    finally:
        conn.close()


def is_user_hacker(user_id: int) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT name, is_hacker FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return False
        if is_owner_admin_name(row["name"]):
            return True
        return bool(row["is_hacker"])
    finally:
        conn.close()


def set_user_hacker(target_id: int, enabled: bool) -> tuple[bool, str]:
    """Gift or revoke the Hacker Panel. Owner cannot lose it."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name FROM users WHERE id = ?",
            (target_id,),
        ).fetchone()
        if not row:
            return False, "Player not found."
        if is_owner_admin_name(row["name"]) and not enabled:
            return False, "Apex always has the Hacker Panel."
        conn.execute(
            "UPDATE users SET is_hacker = ? WHERE id = ?",
            (1 if enabled else 0, target_id),
        )
        conn.commit()
        if enabled:
            return True, f"Hacker Panel gifted to {row['name']}."
        return True, f"Hacker Panel taken from {row['name']}."
    finally:
        conn.close()


def is_user_developer(user_id: int) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT is_developer FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return bool(row["is_developer"]) if row else False
    finally:
        conn.close()


def set_user_developer(target_id: int, enabled: bool) -> tuple[bool, str]:
    """Toggle the Developer role flag (used for the free-hint perk)."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name FROM users WHERE id = ?",
            (target_id,),
        ).fetchone()
        if not row:
            return False, "Player not found."
        conn.execute(
            "UPDATE users SET is_developer = ? WHERE id = ?",
            (1 if enabled else 0, target_id),
        )
        conn.commit()
        if enabled:
            return True, f"Developer role granted to {row['name']}."
        return True, f"Developer role taken from {row['name']}."
    finally:
        conn.close()


def strip_dev_gear(target_id: int) -> tuple[bool, str]:
    """Remove Developer shirt/pants/headset (and the role flag) from a player."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name FROM users WHERE id = ?",
            (target_id,),
        ).fetchone()
        if not row:
            return False, "Player not found."
        removed = []
        for item_id in DEV_ITEM_IDS:
            owned = conn.execute(
                "SELECT 1 FROM inventory WHERE user_id = ? AND item_id = ?",
                (target_id, item_id),
            ).fetchone()
            if not owned:
                continue
            _unequip_item(conn, target_id, item_id)
            conn.execute(
                "DELETE FROM inventory WHERE user_id = ? AND item_id = ?",
                (target_id, item_id),
            )
            conn.execute(
                "DELETE FROM listings WHERE seller_id = ? AND item_id = ?",
                (target_id, item_id),
            )
            item = get_item(item_id)
            removed.append(item["label"] if item else item_id)
        conn.execute(
            "UPDATE users SET is_developer = 0 WHERE id = ?",
            (target_id,),
        )
        conn.commit()
        if not removed:
            return False, f"{row['name']} has no Developer gear."
        return True, f"Removed from {row['name']}: " + ", ".join(removed)
    finally:
        conn.close()


def gift_dev_gear(target_id: int) -> tuple[bool, str]:
    """Give Developer shirt, pants, and headset for free (max 1 owner) and set the role flag."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id, name FROM users WHERE id = ?",
            (target_id,),
        ).fetchone()
        if not row:
            conn.rollback()
            return False, "Player not found."
        owners = _dev_owner_ids(conn)
        if target_id not in owners and len(owners) >= DEV_OWNER_LIMIT:
            conn.rollback()
            return False, "Only 1 player can hold Developer gear. Strip the other one first."
        given = []
        for item_id in DEV_ITEM_IDS:
            conn.execute(
                "INSERT OR IGNORE INTO inventory (user_id, item_id) VALUES (?, ?)",
                (target_id, item_id),
            )
            item = get_item(item_id)
            if item:
                col = slot_column(item["slot"])
                conn.execute(
                    f"UPDATE users SET {col} = ? WHERE id = ?",
                    (item_id, target_id),
                )
                given.append(item["label"])
        conn.execute(
            "UPDATE users SET is_developer = 1 WHERE id = ?",
            (target_id,),
        )
        conn.commit()
        return True, f"Gifted Developer gear to {row['name']}: " + ", ".join(given)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def strip_admin_gear(target_id: int) -> tuple[bool, str]:
    """Remove Admin shirt/pants/crown from a player (not Apex)."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name FROM users WHERE id = ?",
            (target_id,),
        ).fetchone()
        if not row:
            return False, "Player not found."
        if is_owner_admin_name(row["name"]):
            return False, "Cannot strip Admin gear from Apex."
        removed = []
        for item_id in ADMIN_ITEM_IDS:
            owned = conn.execute(
                "SELECT 1 FROM inventory WHERE user_id = ? AND item_id = ?",
                (target_id, item_id),
            ).fetchone()
            if not owned:
                continue
            _unequip_item(conn, target_id, item_id)
            conn.execute(
                "DELETE FROM inventory WHERE user_id = ? AND item_id = ?",
                (target_id, item_id),
            )
            conn.execute(
                "DELETE FROM listings WHERE seller_id = ? AND item_id = ?",
                (target_id, item_id),
            )
            item = get_item(item_id)
            removed.append(item["label"] if item else item_id)
        conn.commit()
        if not removed:
            return False, f"{row['name']} has no Admin shirt/pants/crown."
        return True, f"Removed from {row['name']}: " + ", ".join(removed)
    finally:
        conn.close()


def gift_admin_gear(target_id: int) -> tuple[bool, str]:
    """Give Admin shirt, pants, and crown for free (still max 2 owners)."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id, name FROM users WHERE id = ?",
            (target_id,),
        ).fetchone()
        if not row:
            conn.rollback()
            return False, "Player not found."
        owners = _admin_owner_ids(conn)
        if target_id not in owners and len(owners) >= ADMIN_OWNER_LIMIT:
            conn.rollback()
            return False, "Only 2 players can hold Admin gear. Strip the other buyer first."
        given = []
        for item_id in ADMIN_ITEM_IDS:
            conn.execute(
                "INSERT OR IGNORE INTO inventory (user_id, item_id) VALUES (?, ?)",
                (target_id, item_id),
            )
            item = get_item(item_id)
            if item:
                col = slot_column(item["slot"])
                conn.execute(
                    f"UPDATE users SET {col} = ? WHERE id = ?",
                    (item_id, target_id),
                )
                given.append(item["label"])
        conn.commit()
        return True, f"Gifted Admin gear to {row['name']}: " + ", ".join(given)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def hacker_add_coins(user_id: int, amount: int) -> tuple[bool, str]:
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return False, "Invalid coins."
    if amount < 1 or amount > 1_000_000_000_000_000:
        return False, "Amount must be 1 to 1Q."
    coins = add_coins(user_id, amount)
    return True, f"Hacked +{amount} coins. Balance 🪙 {coins}."


def shade_nuke_all_points() -> tuple[bool, str]:
    """Zero every player's mode stars."""
    conn = get_connection()
    try:
        conn.execute("UPDATE scores SET points = 0")
        conn.commit()
        return True, "All points nuked."
    finally:
        conn.close()


def shade_scorch_leaderboard() -> tuple[bool, str]:
    """Wipe scores table rows (leaderboard empty)."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM scores")
        # re-seed zero rows for remaining users
        users = conn.execute("SELECT id FROM users").fetchall()
        for u in users:
            for mode in ALL_MODES:
                conn.execute(
                    "INSERT OR IGNORE INTO scores (user_id, mode, points) VALUES (?, ?, 0)",
                    (u["id"], mode),
                )
        conn.commit()
        return True, "Leaderboard scorched."
    finally:
        conn.close()


def shade_purge_players(actor_id: int) -> tuple[bool, str]:
    """Delete all non-owner, non-admin players (and fakes)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, is_admin FROM users WHERE id != ?",
            (actor_id,),
        ).fetchall()
        deleted = 0
        for r in rows:
            if is_owner_admin_name(r["name"]):
                continue
            if r["is_admin"]:
                continue
            conn.execute("DELETE FROM unlocks WHERE user_id = ?", (r["id"],))
            conn.execute("DELETE FROM scores WHERE user_id = ?", (r["id"],))
            conn.execute("DELETE FROM activity WHERE user_id = ?", (r["id"],))
            conn.execute("DELETE FROM listings WHERE seller_id = ?", (r["id"],))
            conn.execute("DELETE FROM inventory WHERE user_id = ?", (r["id"],))
            conn.execute("DELETE FROM users WHERE id = ?", (r["id"],))
            deleted += 1
        conn.commit()
        return True, f"Purged {deleted} player(s)."
    finally:
        conn.close()


def shade_factory_reset(actor_id: int) -> tuple[bool, str]:
    """Total wipe except the owner account (Apex)."""
    conn = get_connection()
    try:
        actor = conn.execute(
            "SELECT id, name FROM users WHERE id = ?", (actor_id,)
        ).fetchone()
        if not actor or not is_owner_admin_name(actor["name"]):
            return False, "Only Apex Shade can factory wipe."
        others = conn.execute(
            "SELECT id FROM users WHERE id != ?", (actor_id,)
        ).fetchall()
        for r in others:
            uid = r["id"]
            conn.execute("DELETE FROM unlocks WHERE user_id = ?", (uid,))
            conn.execute("DELETE FROM scores WHERE user_id = ?", (uid,))
            conn.execute("DELETE FROM activity WHERE user_id = ?", (uid,))
            conn.execute("DELETE FROM listings WHERE seller_id = ?", (uid,))
            conn.execute("DELETE FROM inventory WHERE user_id = ?", (uid,))
            conn.execute("DELETE FROM users WHERE id = ?", (uid,))
        # reset owner stats
        conn.execute("UPDATE scores SET points = 0 WHERE user_id = ?", (actor_id,))
        conn.execute("DELETE FROM unlocks WHERE user_id = ?", (actor_id,))
        conn.execute("DELETE FROM activity WHERE user_id = ?", (actor_id,))
        conn.execute(
            "UPDATE users SET coins = 0, god_mode = 0, is_banned = 0 WHERE id = ?",
            (actor_id,),
        )
        conn.commit()
        return True, "Factory death complete. Only Apex remains."
    finally:
        conn.close()


def shade_inject_stats(
    user_id: int,
    *,
    coins: int | None = None,
    points_per_mode: int | None = None,
    mode_scores: dict | None = None,
) -> tuple[bool, str]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "User not found."
        if coins is not None:
            conn.execute(
                "UPDATE users SET coins = ? WHERE id = ?",
                (max(0, int(coins)), user_id),
            )
        if points_per_mode is not None:
            pts = max(0, int(points_per_mode))
            for mode in ALL_MODES:
                conn.execute(
                    """
                    INSERT INTO scores (user_id, mode, points) VALUES (?, ?, ?)
                    ON CONFLICT(user_id, mode) DO UPDATE SET points = excluded.points
                    """,
                    (user_id, mode, pts),
                )
        if mode_scores:
            for mode, pts in mode_scores.items():
                if mode not in ALL_MODES:
                    continue
                conn.execute(
                    """
                    INSERT INTO scores (user_id, mode, points) VALUES (?, ?, ?)
                    ON CONFLICT(user_id, mode) DO UPDATE SET points = excluded.points
                    """,
                    (user_id, mode, max(0, int(pts))),
                )
        conn.commit()
        return True, "Stats injected."
    finally:
        conn.close()


def shade_unlock_all(user_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "User not found."
        for mode in LOCKED_MODES:
            conn.execute(
                "INSERT OR IGNORE INTO unlocks (user_id, mode) VALUES (?, ?)",
                (user_id, mode),
            )
        conn.commit()
        return True, "All modes unlocked."
    finally:
        conn.close()


def shade_force_rank_one(user_id: int) -> tuple[bool, str]:
    """Set this user's scores above every other player in every mode."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "User not found."
        for mode in ALL_MODES:
            top = conn.execute(
                "SELECT MAX(points) AS m FROM scores WHERE mode = ? AND user_id != ?",
                (mode, user_id),
            ).fetchone()
            best = int(top["m"] or 0)
            target = best + 10000
            conn.execute(
                """
                INSERT INTO scores (user_id, mode, points) VALUES (?, ?, ?)
                ON CONFLICT(user_id, mode) DO UPDATE SET points = excluded.points
                """,
                (user_id, mode, target),
            )
        conn.execute(
            "UPDATE users SET coins = MAX(coins, 99999) WHERE id = ?",
            (user_id,),
        )
        conn.commit()
        return True, "Forced #1 on every board."
    finally:
        conn.close()


def shade_reset_my_run(user_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        conn.execute("UPDATE scores SET points = 0 WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM unlocks WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM activity WHERE user_id = ?", (user_id,))
        conn.execute(
            "UPDATE users SET coins = 0, god_mode = 0 WHERE id = ?",
            (user_id,),
        )
        conn.commit()
        return True, "Your run was reset."
    finally:
        conn.close()


def shade_find_user_by_name(name: str):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT id, name, is_admin, is_banned, is_fake FROM users WHERE name = ? COLLATE NOCASE",
            (name.strip(),),
        ).fetchone()
    finally:
        conn.close()


def shade_crush_points(user_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT name FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return False, "User not found."
        if is_owner_admin_name(row["name"]):
            return False, "Cannot crush Apex Shade."
    finally:
        conn.close()
    return admin_reset_scores(user_id)


def shade_ban_user(user_id: int, banned: bool = True) -> tuple[bool, str]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return False, "User not found."
        if is_owner_admin_name(row["name"]):
            return False, "Cannot ban Apex Shade."
        conn.execute(
            "UPDATE users SET is_banned = ? WHERE id = ?",
            (1 if banned else 0, user_id),
        )
        conn.commit()
        return True, ("Banned." if banned else "Unbanned.")
    finally:
        conn.close()


def shade_delete_user(user_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name, is_admin FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return False, "User not found."
        if is_owner_admin_name(row["name"]):
            return False, "Cannot delete Apex Shade."
        conn.execute("DELETE FROM unlocks WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM scores WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM activity WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM listings WHERE seller_id = ?", (user_id,))
        conn.execute("DELETE FROM inventory WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True, "Account deleted."
    finally:
        conn.close()


def shade_spawn_fakes(count: int = 5) -> tuple[bool, str]:
    import random

    count = max(1, min(int(count), 20))
    names = [
        "Nova", "Blitz", "Pixel", "Comet", "Spark", "Luna", "Bolt", "Zest",
        "Mango", "Kit", "Echo", "Frost", "Glow", "Dash", "Quinn",
    ]
    conn = get_connection()
    try:
        made = 0
        for i in range(count):
            base = random.choice(names)
            uname = f"{base}{random.randint(10, 99)}"
            exists = conn.execute(
                "SELECT 1 FROM users WHERE name = ? COLLATE NOCASE", (uname,)
            ).fetchone()
            if exists:
                continue
            cur = conn.execute(
                """
                INSERT INTO users (name, password_hash, coins, is_admin, is_fake)
                VALUES (?, ?, ?, 0, 1)
                """,
                (
                    uname,
                    generate_password_hash("fake-bot"),
                    random.randint(50, 2000),
                ),
            )
            uid = cur.lastrowid
            for mode in ALL_MODES:
                pts = random.randint(10, 5000)
                conn.execute(
                    "INSERT INTO scores (user_id, mode, points) VALUES (?, ?, ?)",
                    (uid, mode, pts),
                )
            made += 1
        conn.commit()
        return True, f"Spawned {made} fake rival(s)."
    finally:
        conn.close()


def shade_clear_fakes() -> tuple[bool, str]:
    conn = get_connection()
    try:
        fakes = conn.execute(
            "SELECT id FROM users WHERE is_fake = 1"
        ).fetchall()
        n = 0
        for r in fakes:
            uid = r["id"]
            conn.execute("DELETE FROM unlocks WHERE user_id = ?", (uid,))
            conn.execute("DELETE FROM scores WHERE user_id = ?", (uid,))
            conn.execute("DELETE FROM activity WHERE user_id = ?", (uid,))
            conn.execute("DELETE FROM listings WHERE seller_id = ?", (uid,))
            conn.execute("DELETE FROM inventory WHERE user_id = ?", (uid,))
            conn.execute("DELETE FROM users WHERE id = ?", (uid,))
            n += 1
        conn.commit()
        return True, f"Cleared {n} fake(s)."
    finally:
        conn.close()


def shade_system_dump() -> dict:
    users = get_all_users()
    stats = get_admin_stats()
    return {
        "stats": stats,
        "users": [
            {
                "id": u["id"],
                "name": u["name"],
                "coins": u["coins"],
                "is_admin": u["is_admin"],
                "is_owner": u.get("is_owner"),
                "is_banned": u.get("is_banned"),
                "is_fake": u.get("is_fake"),
                "god_mode": u.get("god_mode"),
                "is_hacker": u.get("is_hacker"),
                "has_admin_gear": u.get("has_admin_gear"),
                "scores": u["scores"],
                "unlocked": u["unlocked"],
            }
            for u in users
        ],
    }


def get_leaderboard(mode: str, limit: int = 20) -> list[dict]:
    if mode not in ALL_MODES:
        raise ValueError("Invalid mode")
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT u.id AS user_id, u.name, u.equipped_name, s.points
            FROM scores s
            JOIN users u ON u.id = s.user_id
            WHERE s.mode = ? AND s.points > 0
              AND COALESCE(u.is_banned, 0) = 0
            ORDER BY s.points DESC, u.name ASC
            LIMIT ?
            """,
            (mode, limit),
        ).fetchall()
        return [
            {
                "rank": i + 1,
                "user_id": r["user_id"],
                "name": r["name"],
                "points": r["points"],
                "name_style": name_style(r["equipped_name"]),
                "is_owner": is_owner_admin_name(r["name"]),
            }
            for i, r in enumerate(rows)
        ]
    finally:
        conn.close()


def get_coins_leaderboard(limit: int = 20) -> list[dict]:
    """Richest players by wallet coins (excludes banned)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id AS user_id, name, coins, equipped_name
            FROM users
            WHERE coins > 0
              AND COALESCE(is_banned, 0) = 0
            ORDER BY coins DESC, name ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "rank": i + 1,
                "user_id": r["user_id"],
                "name": r["name"],
                "coins": int(r["coins"]),
                "name_style": name_style(r["equipped_name"]),
                "is_owner": is_owner_admin_name(r["name"]),
            }
            for i, r in enumerate(rows)
        ]
    finally:
        conn.close()


CHAT_MAX_LEN = 80
CHAT_COOLDOWN_SEC = 2
CHAT_PAGE = 80
_CHAT_URL_RE = re.compile(r"https?://|www\.", re.I)


def _ensure_review_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS review_words (
            user_id INTEGER NOT NULL,
            mode TEXT NOT NULL,
            word TEXT NOT NULL,
            hits INTEGER NOT NULL DEFAULT 1,
            last_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (user_id, mode, word),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_review_user_time ON review_words(user_id, last_at)"
    )
    cols = {row[1] for row in conn.execute("PRAGMA table_info(review_words)").fetchall()}
    if "first_at" not in cols:
        # Tracks when a word was FIRST answered correctly, separate from last_at
        # (which updates on every repeat review). Needed to count "new words
        # learned this week" for the parent dashboard/weekly email without
        # double-counting words the kid is just reviewing again.
        conn.execute("ALTER TABLE review_words ADD COLUMN first_at TEXT")
        conn.execute("UPDATE review_words SET first_at = last_at WHERE first_at IS NULL")


def record_review_word(user_id: int, mode: str, word: str) -> None:
    """Remember a correctly answered word for later review mix."""
    w = (word or "").strip().lower()[:48]
    if not w or mode not in ALL_MODES:
        return
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO review_words (user_id, mode, word, hits, last_at, first_at)
            VALUES (?, ?, ?, 1, datetime('now'), datetime('now'))
            ON CONFLICT(user_id, mode, word) DO UPDATE SET
                hits = hits + 1,
                last_at = datetime('now')
            """,
            (int(user_id), mode, w),
        )
        conn.commit()
    finally:
        conn.close()


def get_review_words(user_id: int, mode: str, limit: int = 40) -> list[str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT word FROM review_words
            WHERE user_id = ? AND mode = ?
            ORDER BY last_at DESC
            LIMIT ?
            """,
            (int(user_id), mode, int(limit)),
        ).fetchall()
        return [str(r["word"]) for r in rows]
    finally:
        conn.close()


def get_recent_review_words(user_id: int, limit: int = 16) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT word, mode, hits, last_at
            FROM review_words
            WHERE user_id = ?
            ORDER BY last_at DESC
            LIMIT ?
            """,
            (int(user_id), int(limit)),
        ).fetchall()
        return [
            {
                "word": r["word"],
                "mode": r["mode"],
                "hits": int(r["hits"] or 1),
                "last_at": r["last_at"],
            }
            for r in rows
        ]
    finally:
        conn.close()


FLUENCY_MODE = "impossible"
FLUENCY_ATTEMPTS_PER_WEEK = 3


def _ensure_fluency_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fluency_attempts (
            user_id INTEGER NOT NULL,
            taken_at TEXT NOT NULL DEFAULT (datetime('now')),
            passed INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_fluency_user_time ON fluency_attempts(user_id, taken_at)"
    )


SUBSCRIPTION_PRICE_PKR = 1000
SUBSCRIPTION_MONTH_DAYS = 30
SUBSCRIPTION_TRIAL_DAYS = 7
SUBSCRIPTION_METHODS = ("jazzcash", "easypaisa", "card")


def _ensure_subscription_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY,
            is_active INTEGER NOT NULL DEFAULT 0,
            start_date TEXT,
            end_date TEXT,
            method TEXT,
            reference TEXT,
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cols = {row[1] for row in conn.execute("PRAGMA table_info(subscriptions)").fetchall()}
    if "trial_used" not in cols:
        # Tracked separately from is_active/end_date, which naturally go stale
        # once a trial expires — this stays permanently true so the free week
        # can't just be re-claimed by starting it again.
        conn.execute("ALTER TABLE subscriptions ADD COLUMN trial_used INTEGER NOT NULL DEFAULT 0")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS subscription_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            method TEXT NOT NULL,
            reference TEXT,
            note TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            resolved_at TEXT,
            resolved_by TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sub_requests_status ON subscription_requests(status)"
    )


def get_subscription(user_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT is_active, start_date, end_date, method FROM subscriptions WHERE user_id = ?",
            (int(user_id),),
        ).fetchone()
        if not row:
            return {"is_active": False, "start_date": None, "end_date": None, "method": None}
        active = bool(row["is_active"]) and bool(row["end_date"])
        return {
            "is_active": active,
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "method": row["method"],
        }
    finally:
        conn.close()


def is_subscribed(user_id: int) -> bool:
    """True if the account has a paid subscription that hasn't expired yet."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT 1 FROM subscriptions
            WHERE user_id = ? AND is_active = 1 AND end_date >= date('now')
            """,
            (int(user_id),),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def activate_subscription(
    user_id: int, months: int = 1, method: str | None = None, reference: str | None = None
) -> tuple[bool, str]:
    """Owner/admin action: grant or extend a subscription. Stacks on top of any
    remaining time rather than overwriting it, so an early renewal isn't wasted."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE id = ?", (int(user_id),)
        ).fetchone()
        if not row:
            return False, "User not found."
        existing = conn.execute(
            "SELECT end_date FROM subscriptions WHERE user_id = ?", (int(user_id),)
        ).fetchone()
        base = "date('now')"
        if existing and existing["end_date"]:
            base = "MAX(date('now'), date(?))"
        days = int(months) * SUBSCRIPTION_MONTH_DAYS
        if existing and existing["end_date"]:
            conn.execute(
                f"""
                INSERT INTO subscriptions (user_id, is_active, start_date, end_date, method, reference, updated_at)
                VALUES (?, 1, date('now'), date({base}, ? || ' days'), ?, ?, datetime('now'))
                ON CONFLICT(user_id) DO UPDATE SET
                    is_active = 1,
                    end_date = date({base}, ? || ' days'),
                    method = excluded.method,
                    reference = excluded.reference,
                    updated_at = datetime('now')
                """,
                (
                    int(user_id), existing["end_date"], f"+{days}", method, reference,
                    existing["end_date"], f"+{days}",
                ),
            )
        else:
            conn.execute(
                f"""
                INSERT INTO subscriptions (user_id, is_active, start_date, end_date, method, reference, updated_at)
                VALUES (?, 1, date('now'), date('now', ? || ' days'), ?, ?, datetime('now'))
                ON CONFLICT(user_id) DO UPDATE SET
                    is_active = 1,
                    start_date = date('now'),
                    end_date = date('now', ? || ' days'),
                    method = excluded.method,
                    reference = excluded.reference,
                    updated_at = datetime('now')
                """,
                (int(user_id), f"+{days}", method, reference, f"+{days}"),
            )
        conn.commit()
        return True, "Subscription activated."
    finally:
        conn.close()


def has_used_trial(user_id: int) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT trial_used FROM subscriptions WHERE user_id = ?", (int(user_id),)
        ).fetchone()
        return bool(row and row["trial_used"])
    finally:
        conn.close()


def start_free_trial(user_id: int) -> tuple[bool, str]:
    """Self-serve, one-time 7-day free trial — no owner approval needed, since
    nothing is being paid. Once trial_used is set it stays set forever, even
    after the trial expires, so it can't just be re-claimed by starting it
    again (unlike a paid subscription, which is fine to stack/renew)."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (int(user_id),)).fetchone()
        if not row:
            return False, "User not found."
        existing = conn.execute(
            "SELECT trial_used, is_active, end_date FROM subscriptions WHERE user_id = ?",
            (int(user_id),),
        ).fetchone()
        if existing and existing["trial_used"]:
            return False, "You've already used your free trial."
        if existing and existing["is_active"] and existing["end_date"] and existing["end_date"] >= _today():
            return False, "You're already subscribed."
        conn.execute(
            """
            INSERT INTO subscriptions (user_id, is_active, start_date, end_date, method, reference, trial_used, updated_at)
            VALUES (?, 1, date('now'), date('now', ?), 'trial', 'free trial', 1, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                is_active = 1,
                start_date = date('now'),
                end_date = date('now', ?),
                method = 'trial',
                reference = 'free trial',
                trial_used = 1,
                updated_at = datetime('now')
            """,
            (int(user_id), f"+{SUBSCRIPTION_TRIAL_DAYS} days", f"+{SUBSCRIPTION_TRIAL_DAYS} days"),
        )
        conn.commit()
        return True, f"Free {SUBSCRIPTION_TRIAL_DAYS}-day trial started!"
    finally:
        conn.close()


def revoke_subscription(user_id: int) -> tuple[bool, str]:
    """Owner action: undo an accidental free grant, or cancel a subscription."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT user_id FROM subscriptions WHERE user_id = ?", (int(user_id),)
        ).fetchone()
        if not row:
            return False, "This account was never subscribed."
        conn.execute(
            "UPDATE subscriptions SET is_active = 0, updated_at = datetime('now') WHERE user_id = ?",
            (int(user_id),),
        )
        conn.commit()
        return True, "Subscription removed."
    finally:
        conn.close()


def create_subscription_request(
    user_id: int, method: str, reference: str, note: str = ""
) -> tuple[bool, str | int]:
    """Parent reports "I sent the payment" — creates a pending row for the owner
    to confirm against their JazzCash/EasyPaisa account before activating."""
    method = (method or "").strip().lower()
    if method not in SUBSCRIPTION_METHODS:
        return False, "Please choose a payment method."
    reference = (reference or "").strip()[:120]
    note = (note or "").strip()[:300]
    if method in ("jazzcash", "easypaisa") and not reference:
        return False, "Please enter the transaction ID from your payment app."
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM subscription_requests WHERE user_id = ? AND status = 'pending'",
            (int(user_id),),
        ).fetchone()
        if existing:
            return False, "You already have a payment waiting for approval."
        cur = conn.execute(
            """
            INSERT INTO subscription_requests (user_id, method, reference, note)
            VALUES (?, ?, ?, ?)
            """,
            (int(user_id), method, reference, note),
        )
        conn.commit()
        return True, cur.lastrowid
    finally:
        conn.close()


def get_pending_subscription_request(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id, method, reference, note, created_at FROM subscription_requests
            WHERE user_id = ? AND status = 'pending'
            ORDER BY created_at DESC LIMIT 1
            """,
            (int(user_id),),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_pending_subscription_requests() -> list[dict]:
    """For the admin panel: every parent-reported payment awaiting approval."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT sr.id, sr.user_id, u.name, sr.method, sr.reference, sr.note, sr.created_at
            FROM subscription_requests sr
            JOIN users u ON u.id = sr.user_id
            WHERE sr.status = 'pending'
            ORDER BY sr.created_at ASC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def resolve_subscription_request(
    request_id: int, approve: bool, actor_name: str
) -> tuple[bool, str]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, user_id, status FROM subscription_requests WHERE id = ?",
            (int(request_id),),
        ).fetchone()
        if not row:
            return False, "Request not found."
        if row["status"] != "pending":
            return False, "Already resolved."
        conn.execute(
            """
            UPDATE subscription_requests
            SET status = ?, resolved_at = datetime('now'), resolved_by = ?
            WHERE id = ?
            """,
            ("approved" if approve else "rejected", actor_name, int(request_id)),
        )
        conn.commit()
    finally:
        conn.close()
    if approve:
        return activate_subscription(row["user_id"], months=1)
    return True, "Payment request rejected."


def count_family_mastered(user_id: int) -> int:
    """Distinct Family phrases this user has gotten correct at least once."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(DISTINCT word) AS c FROM review_words WHERE user_id = ? AND mode = ?",
            (int(user_id), FLUENCY_MODE),
        ).fetchone()
        return int(row["c"] or 0) if row else 0
    finally:
        conn.close()


def is_fluent_unlocked(user_id: int) -> bool:
    import words

    return count_family_mastered(user_id) >= len(words.IMPOSSIBLE_PHRASES)


def recent_fluency_attempt_count(user_id: int, days: int = 7) -> int:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c FROM fluency_attempts
            WHERE user_id = ? AND taken_at >= datetime('now', ?)
            """,
            (int(user_id), f"-{int(days)} days"),
        ).fetchone()
        return int(row["c"] or 0) if row else 0
    finally:
        conn.close()


def record_fluency_attempt(user_id: int, passed: bool) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO fluency_attempts (user_id, passed) VALUES (?, ?)",
            (int(user_id), 1 if passed else 0),
        )
        conn.commit()
    finally:
        conn.close()


def has_fluent_badge(user_id: int) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM user_badges WHERE user_id = ? AND badge_id = 'fluent'",
            (int(user_id),),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


BADGE_DEFS = (
    {"id": "first_star", "emoji": "⭐", "label": "First star"},
    {"id": "heart", "emoji": "❤️", "label": "I like words"},
    {"id": "streak3", "emoji": "🔥", "label": "3-day streak"},
    {"id": "ten", "emoji": "📚", "label": "10 words"},
    {"id": "daily", "emoji": "🌞", "label": "Word of the day"},
    {"id": "space", "emoji": "🚀", "label": "Space catcher"},
    {"id": "shopper", "emoji": "👕", "label": "Dressed up"},
    {"id": "fluent", "emoji": "🎓", "label": "Fluent"},
)


def _ensure_badge_tables(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_badges (
            user_id INTEGER NOT NULL,
            badge_id TEXT NOT NULL,
            earned_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (user_id, badge_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_word (
            user_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            word TEXT NOT NULL,
            UNIQUE (user_id, day),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )


def grant_badge(user_id: int, badge_id: str) -> bool:
    ids = {b["id"] for b in BADGE_DEFS}
    if badge_id not in ids:
        return False
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO user_badges (user_id, badge_id)
            VALUES (?, ?)
            """,
            (int(user_id), badge_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_user_badges(user_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT badge_id, earned_at FROM user_badges
            WHERE user_id = ?
            """,
            (int(user_id),),
        ).fetchall()
        have = {r["badge_id"]: r["earned_at"] for r in rows}
    finally:
        conn.close()
    out = []
    for b in BADGE_DEFS:
        out.append({**b, "earned": b["id"] in have, "earned_at": have.get(b["id"])})
    return out


def refresh_badges(user_id: int) -> None:
    scores = get_user_scores(user_id)
    total = sum(int(v or 0) for v in scores.values())
    if total > 0:
        grant_badge(user_id, "first_star")
    likes = get_word_likes(user_id)
    if likes["liked"]:
        grant_badge(user_id, "heart")
    prog = get_user_progress(user_id)
    if int(prog.get("streak") or 0) >= 3:
        grant_badge(user_id, "streak3")
    conn = get_connection()
    try:
        n = conn.execute(
            "SELECT COUNT(*) AS c FROM review_words WHERE user_id = ?",
            (int(user_id),),
        ).fetchone()
        inv = conn.execute(
            "SELECT COUNT(*) AS c FROM inventory WHERE user_id = ?",
            (int(user_id),),
        ).fetchone()
    finally:
        conn.close()
    if n and int(n["c"] or 0) >= 10:
        grant_badge(user_id, "ten")
    if inv and int(inv["c"] or 0) >= 4:
        grant_badge(user_id, "shopper")


def claim_daily_word(user_id: int, word: str) -> bool:
    """True if this is the first time today they got the daily word right."""
    w = (word or "").strip().lower()
    if not w:
        return False
    day = _today()
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT word FROM daily_word WHERE user_id = ? AND day = ?",
            (int(user_id), day),
        ).fetchone()
        if row:
            conn.commit()
            return False
        conn.execute(
            "INSERT INTO daily_word (user_id, day, word) VALUES (?, ?, ?)",
            (int(user_id), day, w),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def daily_word_done(user_id: int) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM daily_word WHERE user_id = ? AND day = ?",
            (int(user_id), _today()),
        ).fetchone()
        return bool(row)
    finally:
        conn.close()


def _ensure_likes_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS word_likes (
            user_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            liked INTEGER NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (user_id, word),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )


def set_word_like(user_id: int, word: str, liked: bool) -> None:
    w = (word or "").strip().lower()[:48]
    if not w:
        return
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO word_likes (user_id, word, liked, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(user_id, word) DO UPDATE SET
                liked = excluded.liked,
                updated_at = datetime('now')
            """,
            (int(user_id), w, 1 if liked else 0),
        )
        conn.commit()
    finally:
        conn.close()


def get_word_likes(user_id: int) -> dict:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT word, liked FROM word_likes
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (int(user_id),),
        ).fetchall()
        liked = [r["word"] for r in rows if int(r["liked"] or 0) == 1]
        disliked = [r["word"] for r in rows if int(r["liked"] or 0) == 0]
        return {"liked": liked, "disliked": disliked}
    finally:
        conn.close()


def _ensure_chat_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            to_user_id INTEGER,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (to_user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_chat_id ON chat_messages(id)"
    )


def get_player_profile(user_id: int) -> dict | None:
    """Public Apex ID card: name animation, owner, coins, stars."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id, name, coins, equipped_name, aura, is_admin, is_banned
            FROM users WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
        if not row or row["is_banned"]:
            return None
        snap = {
            "id": int(row["id"]),
            "name": row["name"],
            "coins": int(row["coins"] or 0),
            "equipped_name": row["equipped_name"],
            "aura": row["aura"],
            "is_admin": bool(row["is_admin"]),
        }
    finally:
        conn.close()

    scores = get_user_scores(user_id)
    stars = sum(int(v or 0) for v in scores.values())
    avatar = get_avatar(user_id)
    return {
        "user_id": snap["id"],
        "name": snap["name"],
        "apex_id": snap["name"],
        "coins": snap["coins"],
        "stars": stars,
        "scores": scores,
        "name_style": name_style(snap["equipped_name"]),
        "is_owner": is_owner_admin_name(snap["name"]),
        "is_admin": snap["is_admin"],
        "aura": normalize_aura(snap["aura"]) if snap["aura"] else None,
        "avatar": avatar,
    }


def _chat_user_public(row) -> dict:
    return {
        "user_id": int(row["user_id"]),
        "name": row["name"],
        "name_style": name_style(row["equipped_name"]),
        "is_owner": is_owner_admin_name(row["name"]),
    }


def sanitize_chat(body: str) -> tuple[bool, str]:
    text = " ".join((body or "").split())
    # Remove common HTML/Script tags and characters to prevent XSS and injection
    # Even though Jinja2 escapes, this provides a first layer of defense.
    for char in ("<", ">", "{", "}", "[", "]", "script", "iframe", "object"):
        text = text.replace(char, "")
    if not text:
        return False, "Type a message."
    if len(text) > CHAT_MAX_LEN:
        return False, f"Keep it under {CHAT_MAX_LEN} letters."
    if _CHAT_URL_RE.search(text):
        return False, "No links in chat."
    return True, text


def get_chat_messages(
    viewer_id: int, with_user_id: int | None = None, after_id: int = 0
) -> list[dict]:
    conn = get_connection()
    try:
        # On a fresh page load (after_id=0) a long-running conversation can
        # have far more than CHAT_PAGE messages — ORDER BY id ASC LIMIT would
        # return the OLDEST page instead of the recent tail the kid actually
        # wants to see, making it look like the conversation "lost" messages
        # on return. Grab the most recent page, then re-sort ascending for
        # display. Live polling (after_id > 0) is unaffected and stays ASC.
        order = "DESC" if after_id <= 0 else "ASC"
        if with_user_id:
            rows = conn.execute(
                f"""
                SELECT m.id, m.sender_id, m.to_user_id, m.body, m.created_at,
                       u.name, u.equipped_name, u.id AS user_id
                FROM chat_messages m
                JOIN users u ON u.id = m.sender_id
                WHERE (
                    (m.sender_id = ? AND m.to_user_id = ?)
                    OR (m.sender_id = ? AND m.to_user_id = ?)
                )
                  AND m.id > ?
                  AND COALESCE(u.is_banned, 0) = 0
                ORDER BY m.id {order}
                LIMIT ?
                """,
                (
                    viewer_id,
                    with_user_id,
                    with_user_id,
                    viewer_id,
                    after_id,
                    CHAT_PAGE,
                ),
            ).fetchall()
        else:
            rows = conn.execute(
                f"""
                SELECT m.id, m.sender_id, m.to_user_id, m.body, m.created_at,
                       u.name, u.equipped_name, u.id AS user_id
                FROM chat_messages m
                JOIN users u ON u.id = m.sender_id
                WHERE m.to_user_id IS NULL
                  AND m.id > ?
                  AND COALESCE(u.is_banned, 0) = 0
                ORDER BY m.id {order}
                LIMIT ?
                """,
                (after_id, CHAT_PAGE),
            ).fetchall()
        if order == "DESC":
            rows = list(reversed(rows))
        out = []
        for r in rows:
            msg = _chat_user_public(r)
            msg.update(
                {
                    "id": int(r["id"]),
                    "sender_id": int(r["sender_id"]),
                    "to_user_id": r["to_user_id"],
                    "body": r["body"],
                    "created_at": r["created_at"],
                    "mine": int(r["sender_id"]) == viewer_id,
                }
            )
            out.append(msg)
        return out
    finally:
        conn.close()


def get_unread_dm_status(user_id: int) -> dict:
    """Highest direct-message id addressed to this user, for a lightweight
    site-wide "new message" notification (not a full read-receipt system —
    good enough for a kid chatting with one or two friends/siblings)."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT m.id, u.name
            FROM chat_messages m
            JOIN users u ON u.id = m.sender_id
            WHERE m.to_user_id = ?
              AND COALESCE(u.is_banned, 0) = 0
            ORDER BY m.id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        if not row:
            return {"max_id": 0, "from_name": None}
        return {"max_id": int(row["id"]), "from_name": row["name"]}
    finally:
        conn.close()


def post_chat(
    sender_id: int, body: str, to_user_id: int | None = None
) -> tuple[bool, str | dict]:
    ok, cleaned = sanitize_chat(body)
    if not ok:
        return False, cleaned
    if to_user_id is not None:
        try:
            to_user_id = int(to_user_id)
        except (TypeError, ValueError):
            return False, "Unknown player."
        if to_user_id == sender_id:
            return False, "Pick someone else to chat with."
        other = get_player_profile(to_user_id)
        if not other:
            return False, "That player is gone."

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        last = conn.execute(
            """
            SELECT created_at FROM chat_messages
            WHERE sender_id = ?
            ORDER BY id DESC LIMIT 1
            """,
            (sender_id,),
        ).fetchone()
        if last:
            too_soon = conn.execute(
                """
                SELECT (julianday('now') - julianday(?)) * 86400.0 < ?
                """,
                (last["created_at"], CHAT_COOLDOWN_SEC),
            ).fetchone()
            if too_soon and list(too_soon)[0]:
                conn.rollback()
                return False, "Wait a second…"
        cur = conn.execute(
            """
            INSERT INTO chat_messages (sender_id, to_user_id, body)
            VALUES (?, ?, ?)
            """,
            (sender_id, to_user_id, cleaned),
        )
        msg_id = cur.lastrowid
        row = conn.execute(
            """
            SELECT m.id, m.sender_id, m.to_user_id, m.body, m.created_at,
                   u.name, u.equipped_name, u.id AS user_id
            FROM chat_messages m
            JOIN users u ON u.id = m.sender_id
            WHERE m.id = ?
            """,
            (msg_id,),
        ).fetchone()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    payload = _chat_user_public(row)
    payload.update(
        {
            "id": int(row["id"]),
            "sender_id": int(row["sender_id"]),
            "to_user_id": row["to_user_id"],
            "body": row["body"],
            "created_at": row["created_at"],
            "mine": True,
        }
    )
    return True, payload


def get_spin_status(user_id: int) -> dict:
    """Free spin availability + coin balance + cost."""
    day = _today()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT coins, last_free_spin FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return {
                "free_available": False,
                "coins": 0,
                "spin_cost": SPIN_COST,
                "segments": [
                    {"id": s["id"], "label": s["label"]} for s in SPIN_SEGMENTS
                ],
            }
        last = row["last_free_spin"]
        free_available = last != day
        if is_user_god(user_id):
            free_available = True
        return {
            "free_available": free_available,
            "coins": int(row["coins"]),
            "spin_cost": SPIN_COST,
            "segments": [{"id": s["id"], "label": s["label"]} for s in SPIN_SEGMENTS],
        }
    finally:
        conn.close()


def do_lucky_spin(user_id: int, use_paid: bool = False) -> tuple[bool, str | dict]:
    """
    Run one lucky spin. Prefer free daily spin; otherwise spend SPIN_COST.
    Returns prize payload for the client animation.
    """
    import random

    day = _today()
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT coins, last_free_spin, god_mode FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            conn.rollback()
            return False, "User not found."

        coins = int(row["coins"])
        last = row["last_free_spin"]
        god = bool(row["god_mode"]) if "god_mode" in row.keys() else False
        free_ok = (last != day) or god

        paid = False
        if free_ok and not use_paid:
            # free spin
            if not god:
                conn.execute(
                    "UPDATE users SET last_free_spin = ? WHERE id = ?",
                    (day, user_id),
                )
        else:
            # paid spin
            if god:
                paid = True
            elif coins < SPIN_COST:
                conn.rollback()
                return False, f"Need {SPIN_COST} coins for another spin (or wait for free spin tomorrow)."
            else:
                conn.execute(
                    "UPDATE users SET coins = coins - ? WHERE id = ?",
                    (SPIN_COST, user_id),
                )
                coins -= SPIN_COST
                paid = True

        # Weighted pick
        weights = [s["weight"] for s in SPIN_SEGMENTS]
        idx = random.choices(range(len(SPIN_SEGMENTS)), weights=weights, k=1)[0]
        prize = SPIN_SEGMENTS[idx]
        won = int(prize.get("amount") or 0)

        if won > 0:
            conn.execute(
                "UPDATE users SET coins = coins + ? WHERE id = ?",
                (won, user_id),
            )
            coins = coins + won

        conn.commit()

        # log activity coins when won
        if won > 0:
            log_activity(user_id, coins_earned=won)

        # re-read free status
        free_left = False
        if god:
            free_left = True
        else:
            r2 = conn.execute(
                "SELECT last_free_spin FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            free_left = (r2["last_free_spin"] if r2 else None) != day

        return True, {
            "index": idx,
            "label": prize["label"],
            "kind": prize["kind"],
            "amount": won,
            "coins": coins,
            "paid": paid,
            "free_available": free_left,
            "spin_cost": SPIN_COST,
            "message": (
                f"You won {won} coins!"
                if won > 0
                else "Try again — better luck next spin!"
            ),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()