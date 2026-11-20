from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_auth_provider import UserAuthProvider
from app.services.google_auth import verify_google_token


def authenticate_google_user(db: Session, id_token: str) -> User:
    payload = verify_google_token(id_token)

    google_user_id = payload["sub"]
    email = payload.get("email", "").strip().lower()
    name = payload.get("name") or "FinTrack User"
    email_verified = payload.get("email_verified", False)

    # Find an existing Google identity.
    provider_identity = db.scalar(
        select(UserAuthProvider).where(
            UserAuthProvider.provider == "google",
            UserAuthProvider.provider_user_id == google_user_id,
        )
    )

    if provider_identity:
        user = db.get(User, provider_identity.user_id)

        if user is None or not user.is_active:
            raise ValueError("User account is unavailable")

        return user

    # A new Google identity must have a verified email.
    if not email or not email_verified:
        raise ValueError("A verified Google email is required")

    # Do not automatically link an existing password account.
    existing_user = db.scalar(
        select(User).where(
            func.lower(User.email) == email
        )
    )

    if existing_user:
        raise ValueError(
            "An account with this email already exists. "
            "Please log in using your existing method first."
        )

    # Create a new FinTrack user.
    user = User(
        name=name,
        email=email,
        username=None,
        password_hash=None,
        is_active=True,
    )

    db.add(user)
    db.flush()

    # Link the Google identity.
    provider = UserAuthProvider(
        user_id=user.id,
        provider="google",
        provider_user_id=google_user_id,
        provider_email=email,
        email_verified=True,
    )

    db.add(provider)

    return user