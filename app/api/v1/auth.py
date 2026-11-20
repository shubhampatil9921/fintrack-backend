from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
)
from app.schemas.auth import RefreshRequest, LogoutRequest
from app.services.token_service import (
    create_refresh_token,
    rotate_refresh_token,
    revoke_refresh_token,
)
from app.services.auth_service import (
    register_user,
    authenticate_user,
    create_user_token,
)
from app.api.deps import get_current_user
from sqlalchemy.exc import IntegrityError

from app.schemas.auth import GoogleLoginRequest

from app.services.social_auth_service import authenticate_google_user

from app.services.token_service import create_refresh_token
from app.services.auth_service import create_user_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db),
):
    try:
        return register_user(db, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already registered",
        )


@router.post("/login", response_model=TokenResponse)
def login(
    data: UserLogin,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        data.identifier,
        data.password,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username/email or password",
        )

    access_token = create_user_token(user)
    refresh_token = create_refresh_token(db, user)

    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/refresh")
def refresh(
    data: RefreshRequest,
    db: Session = Depends(get_db),
):
    result = rotate_refresh_token(db, data.refresh_token)

    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )

    return result


@router.post("/logout")
def logout(
    data: LogoutRequest,
    db: Session = Depends(get_db),
):
    revoke_refresh_token(db, data.refresh_token)

    return {
        "message": "Logged out successfully",
    }

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user=Depends(get_current_user),
):
    return current_user

@router.post("/google", response_model=TokenResponse)
def google_login(
    data: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    try:
        user = authenticate_google_user(
            db,
            data.id_token,
        )

        access_token = create_user_token(user)
        refresh_token = create_refresh_token(db, user)

        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    except ValueError as e:
        db.rollback()

        raise HTTPException(
            status_code=401,
            detail=str(e),
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Unable to create or link Google account",
        )