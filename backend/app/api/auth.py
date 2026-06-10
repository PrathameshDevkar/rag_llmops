from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.login_auth import LoginRequest
from backend.app.models.user import User
from backend.app.core.security import verify_password
from backend.app.core.auth import create_access_token
from backend.app.repositories.user_repository import UserRepository

router=APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login(
    credentials: LoginRequest,
    db: Session=Depends(get_db)
):
    print("inside the login")
    print("*"*20)
    print("credentials are",credentials)
    
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(credentials.username)
    
    if not user or not verify_password(credentials.password,str(user.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    token= create_access_token(subject=str(user.id))
    
    return {
        "access_token":token,
        "token_type":"bearer"
    }