from utils.security import (
    generate_password,
    hash_password,
    verify_password
)


password = generate_password()

print("Password généré :", password)

hashed = hash_password(password)

print("Hash :", hashed)

is_valid = verify_password(password, hashed)

print("Password valide :", is_valid)