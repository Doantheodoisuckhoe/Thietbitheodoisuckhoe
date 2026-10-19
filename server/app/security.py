"""Băm mật khẩu, JWT cho người dùng, API key cho thiết bị (app gateway)."""
import hashlib
import hmac
import secrets
from datetime import timedelta

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db, utcnow
from .models import CareLink, Device, Patient, User

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_PBKDF2_ITER = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ITER)
    return f"pbkdf2${_PBKDF2_ITER}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, it, salt, h = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(it))
        return hmac.compare_digest(dk.hex(), h)
    except ValueError:
        return False


def create_token(user_id: int) -> str:
    s = get_settings()
    payload = {"sub": str(user_id), "exp": utcnow() + timedelta(hours=s.jwt_expire_hours)}
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def get_current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        user = None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên đăng nhập không hợp lệ",
                            headers={"WWW-Authenticate": "Bearer"})
    return user


# ---------------------------------------------------------------- API key thiết bị
def new_device_key() -> tuple[str, str, str]:
    """Trả về (key đầy đủ – chỉ hiển thị 1 lần, prefix, hash)."""
    key = "hw_" + secrets.token_urlsafe(24)
    return key, key[:11], hashlib.sha256(key.encode()).hexdigest()


def get_device(x_device_key: str = Header(..., alias="X-Device-Key"), db: Session = Depends(get_db)) -> Device:
    h = hashlib.sha256(x_device_key.encode()).hexdigest()
    for dev in db.scalars(select(Device).where(Device.api_key_prefix == x_device_key[:11])):
        if hmac.compare_digest(dev.api_key_hash, h):
            return dev
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key thiết bị không hợp lệ")


# ---------------------------------------------------------------- phân quyền
def can_access_patient(db: Session, user: User, patient_id: int) -> bool:
    if user.role == "admin":
        return True
    return db.scalar(select(CareLink.id).where(CareLink.patient_id == patient_id,
                                               CareLink.user_id == user.id)) is not None


def require_patient(db: Session, user: User, patient_id: int) -> Patient:
    p = db.get(Patient, patient_id)
    if p is None or not can_access_patient(db, user, patient_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy người được theo dõi")
    return p
