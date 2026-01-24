from datetime import datetime, timedelta,timezone
from jose import jwt, JWTError

from backend.app.core.config import SECRET_KEY,ALGORITHM
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User

def create_access_token(subject:str, expires_minutes:int=60) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload={
        "sub":subject,
        "exp":expire
    }
    
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

def decode_access_token(token:str) -> str:
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
    
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/auth/login")

"""
🧠 What this does

Tells FastAPI: “Token comes from Authorization: Bearer header”

Automatically extracts the token string

Powers Swagger’s Authorize 🔒 button
"""

def get_current_user(
    token:str=Depends(oauth2_scheme),
    db: Session=Depends(get_db)
) -> User:
    user_id= decode_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user=db.query(User).filter(User.id==user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user not found"
        )
    
    return user

