"""
Send "come back and play" Web Push notifications to kids who have gone quiet.

Intended to run once a day. Safe to run with push not yet configured: it just
reports 0 sent and exits.

Run:  python tools/send_play_reminders.py

If you're on PythonAnywhere's free plan, its one Scheduled Task slot is
already spent on the weekly parent-report email (see README.md). Rather than
run this script there, hit the equivalent HTTP endpoint from any external
free cron instead (cron-job.org, a GitHub Actions schedule, UptimeRobot):

    curl -X POST https://your-site.pythonanywhere.com/admin/api/push/send-reminders \\
      -H "X-Cron-Key: your-WEEKLY_REPORT_CRON_KEY-value"

This script is for local/self-hosted deployments that have their own cron.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import database as db  # noqa: E402
import push  # noqa: E402

if not push.push_enabled():
    print("Push notifications are not configured (see .env.example) — nothing to do.")
    sys.exit(0)

targets = db.list_inactive_players_with_push()
result = push.send_reminders_batch(targets)
print(
    f"Reminders: sent={result['sent']} removed_stale={result['removed_stale']} "
    f"failed={result['failed']} (of {len(targets)} candidates)"
)
