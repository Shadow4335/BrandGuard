"""Checks Firebase ID tokens from Google sign-in.

Firebase is only the identity proof: once a token is verified, the API looks up (or creates) the BrandGuard account
for that email and issues a normal session, so roles, workspaces and RLS don't change."""
from typing import Optional

from app.config import get_settings

_transport = None  # reused between calls so the HTTP session is shared


def verify_firebase_token(id_token: str) -> Optional[dict]:
    """Claims of a valid ID token for our Firebase project, or None. Signatures are checked against Google's public
    certificates, so only the project ID is needed (no service-account key)."""
    global _transport
    project_id = get_settings().firebase_project_id
    if not (project_id and id_token):
        return None
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import id_token as google_id_token
        _transport = _transport or Request()
        claims = google_id_token.verify_firebase_token(id_token, _transport, audience=project_id)
    except Exception:
        return None
    if not claims or claims.get("iss") != f"https://securetoken.google.com/{project_id}":
        return None
    return claims
