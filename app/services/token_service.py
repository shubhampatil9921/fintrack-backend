import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.jwt import create_access_token
from app.models.refresh_token import RefreshToken, hash_refresh_token
from app.models.user import User


def create_refresh_token(db: Session, user: User) -> str:
    raw_token = secrets.token_urlsafe(64)

    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add(refresh_token)
    db.flush()

    return raw_token


def rotate_refresh_token(db: Session, raw_token: str):
    token_hash = hash_refresh_token(raw_token)

    stored_token = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update()
    )

    if stored_token is None:
        return None

    now = datetime.now(timezone.utc)

    if stored_token.revoked_at is not None:
        return None

    if stored_token.expires_at <= now:
        return None

    user = db.get(User, stored_token.user_id)

    if user is None or not user.is_active:
        return None

    # Invalidate the old token before issuing a replacement.
    stored_token.revoked_at = now

    new_raw_token = create_refresh_token(db, user)
    access_token = create_access_token(user.id)

    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_raw_token,
        "token_type": "bearer",
    }


def revoke_refresh_token(db: Session, raw_token: str) -> bool:
    token_hash = hash_refresh_token(raw_token)

    stored_token = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update()
    )

    if stored_token is None or stored_token.revoked_at is not None:
        return False

    stored_token.revoked_at = datetime.now(timezone.utc)
    db.commit()

    return True