from backend.app.core.security import hash_password, verify_password

def test_hash_password_success():
    password = "password"
    hash = hash_password(password)
    assert password!=hash
    assert verify_password(password,hash) is True
    
def test_verify_password_invalid():
    password = "password"
    hash = hash_password(password)
    assert verify_password("wrong", hash) is False
    
def test_empty_password():
    password = ""
    hashed = hash_password(password)
    assert verify_password("", hashed) is True

def test_long_password():
    password = "A" * 1024
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True