from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.jwt import create_access_token
from app.core.security import hash_password, verify_password
from app.models.user import User


def register_user(db: Session, data):
    email = str(data.email).strip().lower()
    username = data.username.strip().lower()

    existing_user = db.scalar(
        select(User).where(
            or_(
                func.lower(User.email) == email,
                func.lower(User.username) == username,
            )
        )
    )

    if existing_user:
        raise ValueError("Email or username already registered")

    user = User(
        name=data.name.strip(),
        username=username,
        email=email,
        password_hash=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(db: Session, identifier: str, password: str):
    identifier = identifier.strip().lower()

    user = db.scalar(
        select(User).where(
            or_(
                func.lower(User.email) == identifier,
                func.lower(User.username) == identifier,
            )
        )
    )

    if not user or not user.is_active or not user.password_hash:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def create_user_token(user: User) -> str:
    return create_access_token(user.id)