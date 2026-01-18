from app.auth import hash_password, verify_password

def test_password_hashing():
    password = "secure_password_123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert "$" in hashed
    assert verify_password(password, hashed) is True

def test_verify_password_failure():
    password = "secure_password_123"
    hashed = hash_password(password)
    
    assert verify_password("wrong_password", hashed) is False
    assert verify_password("secure_password_123", "invalid_hash_format") is False

def test_verify_password_edge_cases():
    assert verify_password("", "") is False
    assert verify_password("test", None) is False
