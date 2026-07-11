"""SQLite helpers for users, mode scores, coins, and unlocks."""

import os
import sqlite3
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

_DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parent))
DB_PATH = _DATA_DIR / "kids_word_game.db"

FREE_MODES = frozenset({"easy"})
UNLOCK_COSTS = {"normal": 500, "hard": 1500, "top": 5000}
ALL_MODES = ("easy", "normal", "hard", "top")
LOCKED_MODES = tuple(m for m in ALL_MODES if m not in FREE_MODES)


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


def _ensure_admin_user(conn):
    admin_name = os.environ.get("INITIAL_ADMIN_NAME", "Apex").strip()
    if admin_name:
        conn.execute(
            "UPDATE users SET is_admin = 1 WHERE name = ? COLLATE NOCASE",
            (admin_name,),
        )


def _needs_top_mode_migration(conn) -> bool:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='scores'"
    ).fetchone()
    if not row or not row["sql"]:
        return False
    return "'top'" not in row["sql"]


def _migrate_top_mode(conn):
    if not _needs_top_mode_migration(conn):
        for user in conn.execute("SELECT id FROM users").fetchall():
            conn.execute(
                "INSERT OR IGNORE INTO scores (user_id, mode, points) VALUES (?, 'top', 0)",
                (user["id"],),
            )
        return

    conn.executescript(
        """
        CREATE TABLE scores_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mode TEXT NOT NULL CHECK (mode IN ('easy', 'normal', 'hard', 'top')),
            points INTEGER NOT NULL DEFAULT 0,
            UNIQUE (user_id, mode),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        INSERT INTO scores_new (id, user_id, mode, points)
            SELECT id, user_id, mode, points FROM scores;
        INSERT OR IGNORE INTO scores_new (user_id, mode, points)
            SELECT id, 'top', 0 FROM users;
        DROP TABLE scores;
        ALTER TABLE scores_new RENAME TO scores;

        CREATE TABLE unlocks_new (
            user_id INTEGER NOT NULL,
            mode TEXT NOT NULL CHECK (mode IN ('normal', 'hard', 'top')),
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


def init_db():
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        conn.executescript(
            """
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
                mode TEXT NOT NULL CHECK (mode IN ('easy', 'normal', 'hard', 'top')),
                points INTEGER NOT NULL DEFAULT 0,
                UNIQUE (user_id, mode),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS unlocks (
                user_id INTEGER NOT NULL,
                mode TEXT NOT NULL CHECK (mode IN ('normal', 'hard', 'top')),
                unlocked_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (user_id, mode),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        _ensure_user_columns(conn)
        _migrate_top_mode(conn)
        _ensure_admin_user(conn)
        conn.commit()
    finally:
        conn.close()


def create_user(name: str, password: str) -> tuple[bool, str | int]:
    """Create user. Returns (ok, user_id or error message)."""
    name = name.strip()
    if not name:
        return False, "Please enter a name."
    if len(name) > 32:
        return False, "Name is too long."
    if not password or len(password) < 3:
        return False, "Password must be at least 3 characters."

    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
        if existing:
            return False, "That name is already taken."

        cur = conn.execute(
            "INSERT INTO users (name, password_hash, coins) VALUES (?, ?, 0)",
            (name, generate_password_hash(password)),
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
            "SELECT id, name, password_hash, is_admin FROM users WHERE name = ? COLLATE NOCASE",
            (name,),
        ).fetchone()
        if not row or not check_password_hash(row["password_hash"], password):
            return False, "Wrong name or password."
        return True, {
            "id": row["id"],
            "name": row["name"],
            "is_admin": bool(row["is_admin"]),
        }
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
    return {
        "coins": get_user_coins(user_id),
        "unlocked": {mode: mode in unlocked for mode in ALL_MODES},
    }


def is_mode_unlocked(user_id: int, mode: str) -> bool:
    if mode in FREE_MODES:
        return True
    return mode in get_unlocked_modes(user_id)


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
        return int(row["points"]) if row else points
    finally:
        conn.close()


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
                   COALESCE(se.points, 0) AS easy_pts,
                   COALESCE(sn.points, 0) AS normal_pts,
                   COALESCE(sh.points, 0) AS hard_pts,
                   COALESCE(st.points, 0) AS top_pts
            FROM users u
            LEFT JOIN scores se ON se.user_id = u.id AND se.mode = 'easy'
            LEFT JOIN scores sn ON sn.user_id = u.id AND sn.mode = 'normal'
            LEFT JOIN scores sh ON sh.user_id = u.id AND sh.mode = 'hard'
            LEFT JOIN scores st ON st.user_id = u.id AND st.mode = 'top'
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
                "created_at": row["created_at"],
                "scores": {
                    "easy": row["easy_pts"],
                    "normal": row["normal_pts"],
                    "hard": row["hard_pts"],
                    "top": row["top_pts"],
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
            {"id": r["id"], "name": r["name"], "created_at": r["created_at"]}
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

        if user_id == actor_id and not is_admin:
            return False, "You cannot remove your own admin access."

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