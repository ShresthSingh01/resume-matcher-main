import hashlib
import os
import secrets

def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with a random salt.
    Format: salt$hash
    """
    salt = secrets.token_hex(16) # 32 chars
    # iterations=100,000 is decent standard for python's pbkdf2
    pw_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    )
    return f"{salt}${pw_hash.hex()}"

def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Verifies a password against the stored salt$hash.
    """
    if not stored_password or '$' not in stored_password:
        return False
        
    salt, hashed = stored_password.split('$')
    
    check_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        plain_password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    ).hex()
    
    return secrets.compare_digest(check_hash, hashed)
