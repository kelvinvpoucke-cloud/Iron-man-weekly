# Ironman Strava Weekly Report (Route B)

Dit project doet 2 dingen:

1) Een klein web-appje (Flask) met `/auth` waarmee je één keer Strava koppelt.
2) Een wekelijkse job (`weekly.py`) die last-week activiteiten ophaalt en een rapport maakt.
   Optioneel verstuurt hij het rapport per e-mail (SMTP).

## Lokale test (optioneel)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export STRAVA_CLIENT_ID=...
export STRAVA_CLIENT_SECRET=...
export BASE_URL=http://localhost:3000

gunicorn -b 0.0.0.0:3000 app:app
```

Open daarna: http://localhost:3000/auth

## Deploy (Render)
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

Env vars:
- STRAVA_CLIENT_ID
- STRAVA_CLIENT_SECRET
- BASE_URL (https://<jouw-app>.onrender.com)
- (na koppelen) STRAVA_REFRESH_TOKEN
- (optioneel) STRAVA_ATHLETE_ID
- (optioneel e-mail) SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL, TO_EMAIL
