from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate
from backend.app.core.security import hash_password

router = APIRouter(prefix="/users",tags=["users"])
"""prefix="/users" → clean REST API

tags → Swagger grouping

Import schema, not raw dicts
"""

@router.post("",status_code=status.HTTP_201_CREATED)
def create_user(user_in:UserCreate,db: Session = Depends(get_db)):
    print("*"*50)
    print('password hash is',user_in.password)
    print("*"*50)
    user=User(
        username=user_in.username,
        password_hash=hash_password(user_in.password)
    )


    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        # Add this right after db.refresh(user)
        count = db.query(User).count()
        print(f"Total users in DB: {count}")
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="username already exist")

    return {
        "id": str(user.id),
        "username": user.username
    }
