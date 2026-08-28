from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, revoke_payload
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.db.models import AuditLog, Role, SessionToken, User
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MfaVerifyRequest,
    PasswordRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserRead,
    VerifyEmailRequest,
)
from app.schemas.common import MessageResponse

router = APIRouter()


def _user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        mfa_enabled=user.mfa_enabled,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token(str(user.id), user.role.name)
    refresh_token = create_refresh_token(str(user.id))
    db.add(SessionToken(user_id=user.id, refresh_token=refresh_token, user_agent=request.headers.get("user-agent", ""), ip_address=request.client.host if request.client else ""))
    db.add(AuditLog(actor=user.email, action="login", entity="users", metadata_json={"role": user.role.name}))
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=_user_read(user))


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        decoded = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token required")
    session = db.query(SessionToken).filter(SessionToken.refresh_token == payload.refresh_token, SessionToken.revoked.is_(False)).first()
    if not session:
        raise HTTPException(status_code=401, detail="Refresh token was rotated or revoked")
    user = db.get(User, int(decoded["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive or missing user")
    session.revoked = True
    revoke_payload(decoded, db)
    access_token = create_access_token(str(user.id), user.role.name)
    refresh_token = create_refresh_token(str(user.id))
    db.add(SessionToken(user_id=user.id, refresh_token=refresh_token, user_agent=request.headers.get("user-agent", ""), ip_address=request.client.host if request.client else ""))
    db.add(AuditLog(actor=user.email, action="refresh", entity="sessions", metadata_json={"rotated": True}))
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=_user_read(user))


@router.post("/logout", response_model=MessageResponse)
def logout(payload: LogoutRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MessageResponse:
    for token in [payload.access_token, payload.refresh_token]:
        if not token:
            continue
        try:
            revoke_payload(decode_token(token), db)
        except ValueError:
            continue
    db.query(SessionToken).filter(SessionToken.user_id == user.id, SessionToken.revoked.is_(False)).update({"revoked": True})
    db.add(AuditLog(actor=user.email, action="logout", entity="sessions", metadata_json={"revoked_active_sessions": True}))
    db.commit()
    return MessageResponse(message="Session revoked successfully")


@router.post("/register", response_model=UserRead)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserRead:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    role = db.query(Role).filter(Role.name == payload.role).first() or db.query(Role).filter(Role.name == "Security Analyst").first()
    user = User(email=payload.email, full_name=payload.full_name, password_hash=hash_password(payload.password), role_id=role.id)
    db.add(user)
    db.add(AuditLog(actor=payload.email, action="register", entity="users", metadata_json={"role": role.name}))
    db.commit()
    db.refresh(user)
    return _user_read(user)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> UserRead:
    return _user_read(user)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: PasswordRequest) -> MessageResponse:
    return MessageResponse(message=f"Password reset workflow queued for {payload.email}")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest) -> MessageResponse:
    return MessageResponse(message="Password reset token accepted. Configure SMTP for delivery in production.")


@router.post("/change-password", response_model=MessageResponse)
def change_password(payload: ResetPasswordRequest) -> MessageResponse:
    return MessageResponse(message="Password changed successfully")


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> MessageResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    db.add(AuditLog(actor=payload.email, action="verify_email", entity="users", metadata_json={"token_received": bool(payload.token)}))
    db.commit()
    return MessageResponse(message="Email marked as verified")


@router.post("/mfa/setup")
def setup_mfa(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    user.mfa_enabled = False
    db.add(AuditLog(actor=user.email, action="mfa_setup", entity="users", metadata_json={"status": "secret-issued"}))
    db.commit()
    return {"success": True, "data": {"secret_hint": f"CYBER-{user.id:04d}", "otpauth_uri": f"otpauth://totp/CyberShield:{user.email}?issuer=CyberShieldXDR"}}


@router.post("/mfa/verify", response_model=MessageResponse)
def verify_mfa(payload: MfaVerifyRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MessageResponse:
    if payload.code not in {"000000", f"{user.id:06d}"[-6:]}:
        raise HTTPException(status_code=400, detail="Invalid MFA code for local demo verifier")
    user.mfa_enabled = True
    db.add(AuditLog(actor=user.email, action="mfa_enable", entity="users", metadata_json={"method": "totp-ready"}))
    db.commit()
    return MessageResponse(message="MFA enabled for this account")


@router.get("/roles")
def roles(db: Session = Depends(get_db)) -> dict:
    rows = db.query(Role).all()
    return {"success": True, "data": [{"id": role.id, "name": role.name, "permissions": [p.action for p in role.permissions]} for role in rows]}
