from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import PushToken, User
from ..schemas import PushTokenIn, TokenOut, UserCreate, UserOut, UserUpdate
from ..security import create_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã được đăng ký")
    first = (db.scalar(select(func.count(User.id))) or 0) == 0
    user = User(email=email, password_hash=hash_password(body.password), full_name=body.full_name,
                phone=body.phone, role="admin" if first else "caregiver")
    db.add(user)
    db.commit()
    return TokenOut(access_token=create_token(user.id), user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sai email hoặc mật khẩu")
    return TokenOut(access_token=create_token(user.id), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut)
def update_me(body: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.merge(user)
    db.commit()
    return user


@router.post("/push-token", status_code=204)
def register_push_token(body: PushTokenIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tok = db.scalar(select(PushToken).where(PushToken.token == body.token))
    if tok:
        tok.user_id = user.id
        tok.platform = body.platform
    else:
        db.add(PushToken(user_id=user.id, token=body.token, platform=body.platform))
    db.commit()
