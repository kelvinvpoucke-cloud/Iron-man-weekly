import os
import time
from urllib.parse import urlencode

import requests
from flask import Flask, redirect, request

app = Flask(__name__)

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "").strip()
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "").strip()

# Public base URL of your deployed app, e.g. https://your-app.onrender.com
BASE_URL = os.getenv("BASE_URL", "").strip()


def _require_env(var_name: str) -> str:
    val = os.getenv(var_name, "").strip()
    if not val:
        raise RuntimeError(f"Missing environment variable: {var_name}")
    return val


@app.get("/")
def index():
    return (
        "✅ Ironman Strava Weekly Report is running.\n\n"
        "1) Go to /auth to connect Strava.\n"
        "2) After connecting, copy STRAVA_REFRESH_TOKEN into your host env vars.\n"
        "3) Set up a weekly cron to run weekly.py.\n"
    ), 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/auth")
def auth():
    """
    Redirect to Strava OAuth consent screen.
    """
    _require_env("STRAVA_CLIENT_ID")
    # Prefer BASE_URL; if not set, infer from request host.
    base_url = BASE_URL or (request.url_root.rstrip("/"))
    redirect_uri = f"{base_url}/callback"

    # Scope: activity:read_all to include private activities
    params = {
        "client_id": STRAVA_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "approval_prompt": "force",
        "scope": "activity:read_all",
    }
    url = "https://www.strava.com/oauth/authorize?" + urlencode(params)
    return redirect(url)


@app.get("/callback")
def callback():
    """
    Exchange 'code' for tokens.
    Displays the refresh token to copy into your environment variables.
    """
    _require_env("STRAVA_CLIENT_ID")
    _require_env("STRAVA_CLIENT_SECRET")

    err = request.args.get("error")
    if err:
        return f"OAuth error: {err}\n", 400, {"Content-Type": "text/plain; charset=utf-8"}

    code = request.args.get("code")
    if not code:
        return "Missing ?code=\n", 400, {"Content-Type": "text/plain; charset=utf-8"}

    token_url = "https://www.strava.com/api/v3/oauth/token"
    data = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    }
    r = requests.post(token_url, data=data, timeout=30)
    r.raise_for_status()
    payload = r.json()

    refresh_token = payload.get("refresh_token")
    access_token = payload.get("access_token")
    expires_at = payload.get("expires_at")
    athlete = payload.get("athlete") or {}
    athlete_id = athlete.get("id")

    out = []
    out.append("✅ Strava gekoppeld.\n")
    out.append("Zet deze env vars op je hosting (Render):\n")
    out.append(f"STRAVA_REFRESH_TOKEN={refresh_token}\n")
    out.append(f"STRAVA_ATHLETE_ID={athlete_id}\n\n")
    out.append("Let op: bewaar je Client Secret privé.\n")
    out.append(f"(access_token expires_at={expires_at})\n")
    if access_token:
        out.append("\nJe bent klaar. Sluit dit tabblad.\n")

    return "".join(out), 200, {"Content-Type": "text/plain; charset=utf-8"}
