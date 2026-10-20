from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.db import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def token_for(user_id):
    return jwt.encode({"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)}, settings.JWT_SECRET, algorithm="HS256")

async def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: AsyncSession = Depends(get_db)):
    error = HTTPException(401, "请先登录，或重新登录", headers={"WWW-Authenticate": "Bearer"})
    if not credentials:
        raise error
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"], options={"require": ["exp", "sub"]})
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise error
    user = await db.get(User, user_id)
    if not user:
        raise error
    return user
