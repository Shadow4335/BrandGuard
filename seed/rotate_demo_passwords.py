#!/usr/bin/env python3
"""Change the four demo accounts' Supabase passwords to DEMO_USER_PASSWORD.

The first demo password was published in the README and shipped in the browser bundle. Demo users are now signed in by
the server, so their password can be a long random secret that only the backend knows.

To roll it out without breaking the live demo:
  1. Deploy the new backend, then the new frontend.
  2. Put a long random DEMO_USER_PASSWORD in the backend environment (Render) and in backend/.env.
  3. From the repo root run:  backend/.venv/bin/python seed/rotate_demo_passwords.py
  4. Restart or redeploy the backend if the variable was added after step 1.

The password is never printed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import get_settings  # noqa: E402
from app.passwords import MIN_LEN  # noqa: E402
from app.seed_data import USERS  # noqa: E402
from app.store import SupabaseStore  # noqa: E402

PUBLISHED_DEFAULT = "BrandGuard2026!"
MIN_SECRET_LEN = max(MIN_LEN, 20)


def main() -> None:
    s = get_settings()
    if not (s.supabase_url and s.supabase_service_key):
        sys.exit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY in backend/.env first.")
    if s.demo_password == PUBLISHED_DEFAULT:
        sys.exit("DEMO_USER_PASSWORD is unset or still the published default. Set a long random value first.")
    if len(s.demo_password) < MIN_SECRET_LEN:
        sys.exit(f"Use at least {MIN_SECRET_LEN} characters for the demo password (e.g. openssl rand -base64 24).")

    admin = SupabaseStore().client.auth.admin
    by_email = {u.email: u for u in admin.list_users()}
    for demo in USERS:
        account = by_email.get(demo["email"])
        if account is None:
            print("skipped (no such account):", demo["email"])
            continue
        admin.update_user_by_id(account.id, {"password": s.demo_password})
        print("rotated:", demo["email"])
    print("Done. Make sure the backend environment has the same DEMO_USER_PASSWORD.")


if __name__ == "__main__":
    main()
