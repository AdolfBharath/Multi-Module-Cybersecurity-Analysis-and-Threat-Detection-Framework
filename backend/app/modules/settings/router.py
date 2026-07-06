from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import SystemSetting
from app.db.session import get_db

router = APIRouter()


@router.get("")
def get_settings(db: Session = Depends(get_db)) -> dict:
    rows = db.query(SystemSetting).all()
    return {"success": True, "data": {row.key: row.value for row in rows}}


@router.put("/{key}")
def update_setting(key: str, payload: dict, db: Session = Depends(get_db)) -> dict:
    row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if row:
        row.value = payload
    else:
        row = SystemSetting(key=key, value=payload)
        db.add(row)
    db.commit()
    return {"success": True, "data": {key: payload}}

