import os
import smtplib
from email.mime.text import MIMEText
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta, time as dtime
from zoneinfo import ZoneInfo

from strava_client import StravaClient


TZ = os.getenv("TZ_NAME", "Europe/Amsterdam")


def last_week_range_epoch(tz_name: str = TZ) -> Tuple[int, int, str]:
    """
    Returns (after_epoch, before_epoch, label) for last week Monday 00:00 -> this week Monday 00:00.
    """
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)

    # Monday of this week at 00:00
    this_week_monday = (now - timedelta(days=(now.isoweekday() - 1))).replace(hour=0, minute=0, second=0, microsecond=0)
    last_week_monday = this_week_monday - timedelta(weeks=1)

    after = int(last_week_monday.timestamp())
    before = int(this_week_monday.timestamp())
    label = f"{last_week_monday.date().isoformat()} t/m {(this_week_monday.date() - timedelta(days=1)).isoformat()}"
    return after, before, label


def summarize(acts: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
    totals: Dict[str, Dict[str, float]] = {}
    total_seconds = 0.0

    for a in acts:
        sport = a.get("sport_type") or a.get("type") or "Unknown"
        moving = float(a.get("moving_time") or 0)
        dist = float(a.get("distance") or 0)
        elev = float(a.get("total_elevation_gain") or 0)

        if sport not in totals:
            totals[sport] = {"count": 0.0, "seconds": 0.0, "meters": 0.0, "elev": 0.0}
        totals[sport]["count"] += 1
        totals[sport]["seconds"] += moving
        totals[sport]["meters"] += dist
        totals[sport]["elev"] += elev
        total_seconds += moving

    lines = []
    lines.append(f"# Weekrapport ({len(acts)} activiteiten)")
    lines.append("")
    lines.append(f"Totale trainingstijd: {total_seconds/3600:.2f} uur")
    lines.append("")

    for sport, t in sorted(totals.items(), key=lambda kv: kv[1]["seconds"], reverse=True):
        lines.append(
            f"- {sport}: {int(t['count'])}x, {t['seconds']/3600:.2f} u, {t['meters']/1000:.1f} km, {int(round(t['elev']))} hm"
        )

    # Add a compact list of sessions (helpful for quick scan)
    lines.append("")
    lines.append("## Sessies (compact)")
    for a in sorted(acts, key=lambda x: x.get("start_date_local", "")):
        name = a.get("name", "Activity")
        sport = a.get("sport_type") or a.get("type") or "Unknown"
        start_local = a.get("start_date_local", "")[:16].replace("T", " ")
        dist_km = (a.get("distance") or 0) / 1000.0
        moving_min = (a.get("moving_time") or 0) / 60.0
        lines.append(f"- {start_local} — {sport}: {dist_km:.1f} km, {moving_min:.0f} min — {name}")

    report = "\n".join(lines).strip() + "\n"
    meta = {"total_hours": total_seconds/3600, "by_sport": totals}
    return report, meta


def send_email(subject: str, body: str) -> None:
    """
    Send mail via SMTP.
    Required env vars:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL, TO_EMAIL
    """
    required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "FROM_EMAIL", "TO_EMAIL"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing email env vars: {', '.join(missing)}")

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    pw = os.getenv("SMTP_PASS")
    from_email = os.getenv("FROM_EMAIL")
    to_email = os.getenv("TO_EMAIL")

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP(host, port, timeout=30) as s:
        s.ehlo()
        if port == 587:
            s.starttls()
        s.login(user, pw)
        s.sendmail(from_email, [to_email], msg.as_string())


def main() -> None:
    after, before, label = last_week_range_epoch()
    client = StravaClient()
    acts = client.list_activities(after, before)

    report, _ = summarize(acts)

    # Always print to logs (Render cron logs / GitHub Actions logs)
    print(f"=== WEEKRAPPORT {label} ===")
    print(report)

    # Email is optional (if env vars are provided)
    if os.getenv("SMTP_HOST") and os.getenv("TO_EMAIL"):
        subject = f"Ironman weekrapport ({label})"
        send_email(subject, report)
        print("✅ Email sent.")
    else:
        print("ℹ️ Email not configured. Report only printed to logs.")


if __name__ == "__main__":
    main()
