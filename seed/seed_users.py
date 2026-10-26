#!/usr/bin/env python3
"""
Seed script for BrandGuard:
Creates organisation 'Demo Brand' and 4 demo accounts (admin, creator, manager, reviewer).
Idempotent and safe to run multiple times.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Find .env safely without printing contents
for env_path in [
    Path(__file__).resolve().parent.parent / "backend" / ".env",
    Path(__file__).resolve().parent.parent / ".env",
]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
DEMO_PASSWORD = os.getenv("DEMO_USER_PASSWORD", "BrandGuard2026!")

DEMO_USERS = [
    {
        "email": "admin@demo.test",
        "role": "admin",
        "full_name": "Demo Admin",
    },
    {
        "email": "creator@demo.test",
        "role": "creator",
        "full_name": "Demo Creator",
    },
    {
        "email": "manager@demo.test",
        "role": "manager",
        "full_name": "Demo Manager",
    },
    {
        "email": "reviewer@demo.test",
        "role": "reviewer",
        "full_name": "Demo Reviewer",
    },
]


def get_admin_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in backend/.env", file=sys.stderr)
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def seed():
    supabase = get_admin_client()
    print("Connected to Supabase. Checking 'Demo Brand' organisation...")

    # 1. Ensure Organisation exists
    org_res = supabase.table("organisations").select("*").eq("name", "Demo Brand").execute()
    if org_res.data and len(org_res.data) > 0:
        org_id = org_res.data[0]["id"]
        print(f"Found existing organisation 'Demo Brand' (ID: {org_id})")
    else:
        new_org = supabase.table("organisations").insert({"name": "Demo Brand"}).execute()
        if not new_org.data:
            print("Failed to create organisation 'Demo Brand'", file=sys.stderr)
            sys.exit(1)
        org_id = new_org.data[0]["id"]
        print(f"Created new organisation 'Demo Brand' (ID: {org_id})")

    # 2. Query existing auth users
    existing_users = {}
    try:
        users_resp = supabase.auth.admin.list_users()
        if hasattr(users_resp, "users"):
            for u in users_resp.users:
                existing_users[u.email] = u
        elif isinstance(users_resp, list):
            for u in users_resp:
                existing_users[getattr(u, "email", None)] = u
    except Exception as e:
        print(f"Warning: could not list existing auth users ({e}), proceeding with individual checks...")

    # 3. Create or update each demo user
    for spec in DEMO_USERS:
        email = spec["email"]
        role = spec["role"]
        full_name = spec["full_name"]

        user_id = None
        if email in existing_users:
            user = existing_users[email]
            user_id = getattr(user, "id", None)
            print(f"Auth user '{email}' already exists (ID: {user_id}). Updating password...")
            try:
                supabase.auth.admin.update_user_by_id(user_id, {"password": DEMO_PASSWORD})
            except Exception as e:
                print(f"Notice updating user {email}: {e}")
        else:
            print(f"Creating auth user '{email}'...")
            try:
                created = supabase.auth.admin.create_user({
                    "email": email,
                    "password": DEMO_PASSWORD,
                    "email_confirm": True,
                    "user_metadata": {"full_name": full_name, "role": role},
                })
                user_id = created.user.id if hasattr(created, "user") else created.get("id")
                print(f"Created auth user '{email}' (ID: {user_id})")
            except Exception as e:
                # If already exists despite list check
                print(f"Creation notice for {email}: {e}")
                # Try to retrieve ID from profiles or auth
                prof = supabase.table("profiles").select("id").eq("email", email).execute()
                if prof.data:
                    user_id = prof.data[0]["id"]

        if user_id:
            # Upsert into public.profiles
            profile_data = {
                "id": str(user_id),
                "org_id": str(org_id),
                "role": role,
                "email": email,
                "full_name": full_name,
            }
            supabase.table("profiles").upsert(profile_data).execute()
            print(f"Synced profile for '{email}' with role '{role}' in org '{org_id}'")

    print("\n✅ Seed completed successfully!")
    print(f"Default password for demo accounts: {DEMO_PASSWORD}")


if __name__ == "__main__":
    seed()
