from google.auth.transport import requests
from google.oauth2 import id_token

from app.core.config import settings


def verify_google_token(token: str) -> dict:
    client_ids = {
        client_id.strip()
        for client_id in settings.GOOGLE_CLIENT_IDS.split(",")
        if client_id.strip()
    }

    if not client_ids:
        raise ValueError("Google authentication is not configured")

    try:
        payload = id_token.verify_oauth2_token(
            token,
            requests.Request(),
        )

        if payload.get("aud") not in client_ids:
            raise ValueError("Invalid Google token audience")

        if payload.get("iss") not in (
            "accounts.google.com",
            "https://accounts.google.com",
        ):
            raise ValueError("Invalid Google token issuer")

        if not payload.get("sub"):
            raise ValueError("Google user ID is missing")

        if not payload.get("email_verified"):
            raise ValueError("Google email is not verified")

        return payload

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Invalid Google ID token") from exc