"""Send a parent review email when a kid taps Stop."""

from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path


def _from_addr() -> str:
    return (os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER") or "").strip()


def smtp_ready() -> bool:
    return bool(
        os.environ.get("SMTP_HOST")
        and _from_addr()
    )


def build_review_text(
    kid_name: str,
    coins: int,
    learned: list[str],
    mistakes: list[dict],
    started: str | None = None,
) -> str:
    learned_l = [w for w in learned if w]
    miss_l = mistakes or []
    lines = [
        f"Hi,",
        "",
        f"{kid_name} stopped playing Word Stars just now.",
        "",
        f"Coins earned this play: {int(coins or 0)}",
        f"New words they got right: {len(learned_l)}",
        f"Mistakes: {len(miss_l)}",
        "",
        "Words they learned:",
    ]
    if learned_l:
        for w in learned_l:
            lines.append(f"  • {w}")
    else:
        lines.append("  (none yet)")
    lines.append("")
    lines.append("Mistakes:")
    if miss_l:
        for m in miss_l:
            word = (m.get("word") if isinstance(m, dict) else None) or ""
            guess = (m.get("guess") if isinstance(m, dict) else None) or ""
            if guess and guess != word:
                lines.append(f"  • {word} (tried: {guess})")
            else:
                lines.append(f"  • {word}")
    else:
        lines.append("  (no mistakes)")
    if started:
        lines.append("")
        lines.append(f"Started: {started}")
    lines.append(f"Stopped: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("— Word Stars")
    return "\n".join(lines)


def _safe_header_text(text: str) -> str:
    """Strip \\r/\\n before anything reaches an email header — that's how header
    injection works, regardless of whatever validation the caller already did."""
    return (text or "").replace("\r", "").replace("\n", "")


def _send_email(
    to_email: str, subject: str, body: str, log_dir: Path | None = None
) -> tuple[bool, str]:
    """Shared send path for every outgoing parent email (stop-review, weekly
    report, ...). Falls back to a local log file when SMTP isn't configured,
    so the app still "works" (visibly, for a dev) without real credentials."""
    to_email = (to_email or "").strip()
    if not to_email or "@" not in to_email:
        return False, "No parent email on this account."

    subject = _safe_header_text(subject)

    if smtp_ready():
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = _from_addr()
            msg["To"] = to_email
            msg.set_content(body)
            host = os.environ.get("SMTP_HOST", "")
            port = int(os.environ.get("SMTP_PORT") or 587)
            user = (os.environ.get("SMTP_USER") or "").strip()
            password = os.environ.get("SMTP_PASS") or ""
            use_ssl = os.environ.get("SMTP_SSL", "0").lower() in ("1", "true", "yes")
            if use_ssl:
                with smtplib.SMTP_SSL(host, port, timeout=20) as smtp:
                    if user:
                        smtp.login(user, password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(host, port, timeout=20) as smtp:
                    smtp.ehlo()
                    smtp.starttls()
                    if user:
                        smtp.login(user, password)
                    smtp.send_message(msg)
            return True, f"We emailed {to_email}."
        except Exception as exc:
            return False, f"Could not send email ({exc})."

    if log_dir:
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            path = log_dir / "parent_mail.log"
            with path.open("a", encoding="utf-8") as fh:
                fh.write(f"\n--- {datetime.now().isoformat()} to {to_email} ({subject}) ---\n")
                fh.write(body)
                fh.write("\n")
        except OSError:
            pass
    return (
        False,
        "Parent email is saved, but sending is not set up yet. Add SMTP_HOST in .env.",
    )


def send_parent_stop_email(
    to_email: str,
    kid_name: str,
    coins: int,
    learned: list[str],
    mistakes: list[dict],
    started: str | None = None,
    log_dir: Path | None = None,
) -> tuple[bool, str]:
    body = build_review_text(kid_name, coins, learned, mistakes, started)
    subject = f"{_safe_header_text(kid_name)} stopped playing Word Stars"
    return _send_email(to_email, subject, body, log_dir)


def build_weekly_report_text(
    kid_name: str,
    new_words: list[str],
    new_phrases: list[str],
    total_words: int,
    streak: int,
    week_correct: int,
) -> str:
    """The email that's meant to make a parent go 'wow, worth 1000 PKR/month' —
    and worth forwarding to a group chat."""
    lines = [
        f"Hi,",
        "",
        f"Here's how {kid_name} did on Word Stars this week:",
        "",
    ]
    if new_words:
        sample = ", ".join(f"'{w}'" for w in new_words[:6])
        lines.append(f"📚 {len(new_words)} new words learned, including {sample}.")
    else:
        lines.append("📚 No brand-new words this week — a good week to keep the streak going!")
    if new_phrases:
        sample = ", ".join(f"'{p}'" for p in new_phrases[:3])
        lines.append(f"🗣️ Can now say: {sample}.")
    lines.append(f"✅ {week_correct} correct answers this week.")
    if streak >= 2:
        lines.append(f"🔥 {streak}-day play streak!")
    lines.append(f"⭐ {total_words} words learned in total so far.")
    lines.append("")
    lines.append("Keep it up — a few minutes a day adds up fast.")
    lines.append("")
    lines.append("— Word Stars")
    return "\n".join(lines)


def send_weekly_report_email(
    to_email: str,
    kid_name: str,
    new_words: list[str],
    new_phrases: list[str],
    total_words: int,
    streak: int,
    week_correct: int,
    log_dir: Path | None = None,
) -> tuple[bool, str]:
    body = build_weekly_report_text(
        kid_name, new_words, new_phrases, total_words, streak, week_correct
    )
    safe_name = _safe_header_text(kid_name)
    if new_words:
        subject = f"{safe_name} learned {len(new_words)} new words this week! ⭐"
    else:
        subject = f"{safe_name}'s Word Stars weekly report"
    return _send_email(to_email, subject, body, log_dir)
