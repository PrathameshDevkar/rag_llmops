"""Validates JWT lifecycle behaviors, signature validation, and token boundaries"""

from backend.app.core.auth import create_access_token, decode_access_token

def test_create_and_decode_access_token_success():
    subject = "user-1234"
    token = create_access_token(subject = subject)
    decoded_sub = decode_access_token(token = token)
    assert decoded_sub == subject
    
def test_decode_invalid_token():
    assert decode_access_token("completely-invalid-token-string") == ""

def test_decode_empty_token():
    assert decode_access_token("") == ""

def test_expired_token_handling():
    subject = "user-uuid-expired"
    # Create an instantly expired token manually or with negative minutes
    token = create_access_token(subject=subject, expires_minutes=-5)
    assert decode_access_token(token) == ""