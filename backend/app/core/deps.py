from collections.abc import Callable
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.models import Permission, RevokedToken, User
from app.db.session import get_db


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization.split(" ", 1)[1].strip()


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = _extract_bearer(authorization)
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Access token required")
    if db.query(RevokedToken).filter(RevokedToken.jti == payload.get("jti")).first():
        raise HTTPException(status_code=401, detail="Token has been revoked")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive or missing user")
    return user


def require_permissions(*actions: str) -> Callable:
    def dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if user.role.name == "Admin":
            return user
        allowed = {
            permission.action
            for permission in db.query(Permission).filter(Permission.role_id == user.role_id).all()
        }
        missing = [action for action in actions if action not in allowed]
        if missing:
            raise HTTPException(status_code=403, detail=f"Missing permissions: {', '.join(missing)}")
        return user

    return dependency


def revoke_payload(payload: dict, db: Session) -> None:
    expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
    if not db.query(RevokedToken).filter(RevokedToken.jti == payload["jti"]).first():
        db.add(RevokedToken(jti=payload["jti"], token_type=payload.get("type", "unknown"), expires_at=expires_at))


def request_actor(request: Request, user: User | None = None) -> str:
    return user.email if user else request.headers.get("x-api-actor", "anonymous")
