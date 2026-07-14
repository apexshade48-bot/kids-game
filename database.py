"""SQLite helpers for users, mode scores, coins, and unlocks."""

import os
import sqlite3
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

_DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parent))
DB_PATH = _DATA_DIR / "kids_word_game.db"

FREE_MODES = frozenset({"easy"})
UNLOCK_COSTS = {
    "normal": 500,
    "hard": 1500,
    "top": 5000,
    "impossible": 10000,  # adult spoken English track (admin can unlock for free)
}
ALL_MODES = ("easy", "normal", "hard", "top", "impossible")
LOCKED_MODES = tuple(m for m in ALL_MODES if m not in FREE_MODES)
MODE_SQL_LIST = "'easy', 'normal', 'hard', 'top', 'impossible'"
UNLOCK_SQL_LIST = "'normal', 'hard', 'top', 'impossible'"
HINT_COST = 5  # coins to reveal first letter in Spell mode
SPIN_COST = 1000  # coins for an extra lucky spin (after free daily)

# Account aura (theme/skin) — chosen at signup or first login
AURA_IDS = ("violet", "ocean", "forest", "sunset", "candy", "night", "aura")
AURA_CHOICES = (
    {"id": "violet", "label": "Violet Star", "emoji": "💜", "dots": ("#7c3aed", "#f8fafc", "#f59e0b")},
    {"id": "ocean", "label": "Ocean Glow", "emoji": "🌊", "dots": ("#0284c7", "#ecfeff", "#22d3ee")},
    {"id": "forest", "label": "Forest Leaf", "emoji": "🌿", "dots": ("#16a34a", "#f0fdf4", "#86efac")},
    {"id": "sunset", "label": "Sunset Fire", "emoji": "🌅", "dots": ("#ea580c", "#fff7ed", "#fbbf24")},
    {"id": "candy", "label": "Candy Pop", "emoji": "🍬", "dots": ("#db2777", "#fdf2f8", "#f9a8d4")},
    {"id": "night", "label": "Night Sky", "emoji": "🌙", "dots": ("#a78bfa", "#0f172a", "#38bdf8")},
    {"id": "aura", "label": "Mystic Aura", "emoji": "✨", "dots": ("#c084fc", "#fae8ff", "#67e8f9")},
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
    """Ensure scores/unlocks allow top + impossible modes."""
    sql = _scores_sql(conn)
    needs_rebuild = sql and (
        "'impossible'" not in sql or "'top'" not in sql
    )
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
            """
        )
        _ensure_user_columns(conn)
        _migrate_modes_schema(conn)
        _ensure_admin_user(conn)
        conn.commit()
    finally:
        conn.close()


def create_user(name: str, password: str, aura: str | None = None) -> tuple[bool, str | int]:
    """Create user. Returns (ok, user_id or error message)."""
    name = name.strip()
    if not name:
        return False, "Please enter a name."
    if len(name) > 32:
        return False, "Name is too long."
    if not password or len(password) < 3:
        return False, "Password must be at least 3 characters."
    aura_norm = normalize_aura(aura)
    if not aura_norm:
        return False, "Please choose your aura (theme)."

    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
        if existing:
            return False, "That name is already taken."

        cur = conn.execute(
            "INSERT INTO users (name, password_hash, coins, aura) VALUES (?, ?, 0, ?)",
            (name, generate_password_hash(password), aura_norm),
        )
        user_id = cur.lastrowid
        for mode in ALL_MODES:
            conn.execute(
                "INSERT INTO scores (user_id, mode, points) VALUES (?, ?, 0)",
                (user_id, mode),
            )
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
            SELECT id, name, password_hash, is_admin, is_banned, god_mode, aura
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


def get_all_users_progress() -> list[dict]:
    """Progress snapshot for admin panel."""
    users = get_all_users()
    out = []
    for u in users:
        prog = get_user_progress(u["id"])
        out.append({**u, "progress": prog})
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
                   COALESCE(se.points, 0) AS easy_pts,
                   COALESCE(sn.points, 0) AS normal_pts,
                   COALESCE(sh.points, 0) AS hard_pts,
                   COALESCE(st.points, 0) AS top_pts,
                   COALESCE(si.points, 0) AS impossible_pts
            FROM users u
            LEFT JOIN scores se ON se.user_id = u.id AND se.mode = 'easy'
            LEFT JOIN scores sn ON sn.user_id = u.id AND sn.mode = 'normal'
            LEFT JOIN scores sh ON sh.user_id = u.id AND sh.mode = 'hard'
            LEFT JOIN scores st ON st.user_id = u.id AND st.mode = 'top'
            LEFT JOIN scores si ON si.user_id = u.id AND si.mode = 'impossible'
            ORDER BY u.id ASC
            """
        ).fetchall()
        users = []
        for row in rows:
            unlocks = conn.execute(
                "SELECT mode FROM unlocks WHERE user_id = ?", (row["id"],)
            ).fetchall()
            unlocked = list(FREE_MODES) + [u["mode"] for u in unlocks]
            users.append({
                "id": row["id"],
                "name": row["name"],
                "coins": row["coins"],
                "is_admin": bool(row["is_admin"]),
                "is_owner": is_owner_admin_name(row["name"]),
                "is_banned": bool(row["is_banned"]),
                "is_fake": bool(row["is_fake"]),
                "god_mode": bool(row["god_mode"]),
                "created_at": row["created_at"],
                "scores": {
                    "easy": row["easy_pts"],
                    "normal": row["normal_pts"],
                    "hard": row["hard_pts"],
                    "top": row["top_pts"],
                    "impossible": row["impossible_pts"],
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


def admin_set_coins(user_id: int, coins: int) -> tuple[bool, str | int]:
    if coins < 0:
        return False, "Coins cannot be negative."
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "User not found."
        conn.execute("UPDATE users SET coins = ? WHERE id = ?", (coins, user_id))
        conn.commit()
        return True, coins
    finally:
        conn.close()


def admin_grant_unlock(user_id: int, mode: str) -> tuple[bool, str]:
    if mode in FREE_MODES:
        return False, "Easy is always free."
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
        return False, "Easy is always free and cannot be locked."
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
        conn.execute(
            "DELETE FROM unlocks WHERE user_id = ? AND mode IN ('normal', 'hard', 'top', 'impossible')",
            (user_id,),
        )
        conn.commit()
        return True, "Paid modes locked (Normal–Impossible)."
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


def admin_set_password(user_id: int, new_password: str) -> tuple[bool, str]:
    """Admin sets a new password for a player."""
    if not new_password or len(new_password) < 3:
        return False, "Password must be at least 3 characters."
    conn = get_connection()
    try:
        row = conn.execute("SELECT id, name FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False, "User not found."
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
            SELECT u.id AS user_id, u.name, s.points
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
            {"rank": i + 1, "user_id": r["user_id"], "name": r["name"], "points": r["points"]}
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
            SELECT id AS user_id, name, coins
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
            }
            for i, r in enumerate(rows)
        ]
    finally:
        conn.close()


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