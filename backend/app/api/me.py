from fastapi import Depends, APIRouter
from backend.app.core.auth import get_current_user
from backend.app.models.user import User

router=APIRouter(prefix="/me",tags=["me"])

@router.get("")
def read_me(current_user: User=Depends(get_current_user)):
    return {
        "id":str(current_user.id),
        "username":current_user.username
    }
    
    