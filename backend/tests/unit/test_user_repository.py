import pytest
from backend.app.repositories.user_repository import UserRepository
from backend.app.models.user import User
from backend.app.core.security import hash_password

def test_create_user(db_session):
    repo = UserRepository(db_session)
    user = User(username="dev_test", password_hash=hash_password("password"))
    repo.create(user)
    
    assert user.id is not None
    assert repo.count_users() == 1

def test_get_by_username(db_session, test_user):
    repo = UserRepository(db_session)
    fetched = repo.get_by_username(test_user.username)
    assert fetched is not None
    assert fetched.id == test_user.id

def test_get_by_id_not_found(db_session):
    repo = UserRepository(db_session)
    import uuid
    assert repo.get_by_id(str(uuid.uuid4())) is None