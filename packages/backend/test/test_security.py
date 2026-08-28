from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)

# Password hashing
hashed = get_password_hash("mypassword123")
assert hashed != "mypassword123", "Password should be hashed, not stored plain"
assert verify_password("mypassword123", hashed), "Correct password should verify"
assert not verify_password("wrongpassword", hashed), "Wrong password should fail"
print("Password hashing: OK")

# JWT create/decode
token = create_access_token({"sub": "johndoe"})
decoded = decode_access_token(token)
assert decoded["sub"] == "johndoe", "Decoded token should contain the original subject"
assert "exp" in decoded, "Token should carry an expiry claim"
print("JWT create/decode: OK")

print("\nAll security checks passed")