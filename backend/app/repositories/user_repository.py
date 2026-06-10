from sqlalchemy.orm import Session
from backend.app.models.user import User

class UserRepository:
    def __init__(self, db:Session):
        self.db = db
    
    def get_by_id(self, user_id:str) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username:str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()
    
    def create(self, user:User):
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
    
    def count_users(self) -> int:
        return self.db.query(User).count()
    