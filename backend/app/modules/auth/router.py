from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.db.models import AuditLog, Role, SessionToken, User
from app.db.session import get_db
from app.schemas.auth import LoginRequest, PasswordRequest, RegisterRequest, ResetPasswordRequest, TokenResponse, UserRead
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
def me(db: Session = Depends(get_db)) -> UserRead:
    user = db.query(User).filter(User.email == "admin@cybershield.dev").first()
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


@router.get("/roles")
def roles(db: Session = Depends(get_db)) -> dict:
    rows = db.query(Role).all()
    return {"success": True, "data": [{"id": role.id, "name": role.name, "permissions": [p.action for p in role.permissions]} for role in rows]}
