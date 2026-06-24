from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.login_auth import LoginRequest
from backend.app.schemas.user import UserCreate
from backend.app.models.user import User
from backend.app.core.security import verify_password, hash_password
from backend.app.core.auth import create_access_token
from backend.app.repositories.user_repository import UserRepository
from backend.app.core.logging import GLOBAL_LOGGER as log

router=APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(
    credentials: UserCreate,
    db: Session = Depends(get_db)
):
    user_repo = UserRepository(db)

    existing_user = user_repo.get_by_username(username = credentials.username)

    if existing_user:
        log.warning("Username already exist")
        return HTTPException(
            status_code = 400,
            detail = "Username already exist"
        )
    
    try:
        new_user = User(
            username = credentials.username,
            password_hash =  hash_password(credentials.password)
        )

        created_user = user_repo.create(new_user)

        log.info("User registered succesfully")

        return {
            "status": "success",
            "message": "User registered succesfully",
            "user_id": str(new_user.id)
        }
    except Exception as e:
        log.error("User registration failed", error = str(e))
        raise HTTPException (
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while creating your user account"
        )

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