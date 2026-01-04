import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class TokenBundle:
    access_token: str
    expires_at: int
    refresh_token: Optional[str] = None


class StravaClient:
    def __init__(self) -> None:
        self.client_id = os.getenv("STRAVA_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("STRAVA_CLIENT_SECRET", "").strip()
        self.refresh_token = os.getenv("STRAVA_REFRESH_TOKEN", "").strip()

        if not self.client_id or not self.client_secret or not self.refresh_token:
            raise RuntimeError(
                "Missing STRAVA_CLIENT_ID / STRAVA_CLIENT_SECRET / STRAVA_REFRESH_TOKEN env vars"
            )

    def refresh_access_token(self) -> TokenBundle:
        url = "https://www.strava.com/api/v3/oauth/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        r = requests.post(url, data=data, timeout=30)
        r.raise_for_status()
        p = r.json()
        # Strava may rotate refresh_token; keep the latest one.
        return TokenBundle(
            access_token=p["access_token"],
            expires_at=int(p["expires_at"]),
            refresh_token=p.get("refresh_token"),
        )

    def list_activities(self, after_epoch: int, before_epoch: int, per_page: int = 200) -> List[Dict[str, Any]]:
        tb = self.refresh_access_token()
        headers = {"Authorization": f"Bearer {tb.access_token}"}

        acts: List[Dict[str, Any]] = []
        page = 1
        while True:
            params = {
                "after": after_epoch,
                "before": before_epoch,
                "page": page,
                "per_page": per_page,
            }
            r = requests.get("https://www.strava.com/api/v3/athlete/activities", headers=headers, params=params, timeout=30)
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            acts.extend(batch)
            if len(batch) < per_page:
                break
            page += 1
        return acts
