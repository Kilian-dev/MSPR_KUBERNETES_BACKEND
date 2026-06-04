import random
import string
import bcrypt
import pyotp


SPECIAL_CHARS = "!@#$%^&*()-_=+[]{}<>?"


def generate_password():
    lowercase = random.choice(string.ascii_lowercase)
    uppercase = random.choice(string.ascii_uppercase)
    digit = random.choice(string.digits)
    special = random.choice(SPECIAL_CHARS)

    all_characters = (
        string.ascii_letters +
        string.digits +
        SPECIAL_CHARS
    )

    remaining = [
        random.choice(all_characters)
        for _ in range(20)
    ]

    password_list = [
        lowercase,
        uppercase,
        digit,
        special
    ] + remaining

    random.shuffle(password_list)

    return ''.join(password_list)


def hash_password(password: str):
    salt = bcrypt.gensalt()

    hashed = bcrypt.hashpw(
        password.encode('utf-8'),
        salt
    )

    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str):
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def generate_mfa_secret():
    return pyotp.random_base32()


def generate_totp_uri(username: str, secret: str):
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name="COFRAP"
    )


def verify_totp(secret: str, code: str):
    totp = pyotp.TOTP(secret)
    return totp.verify(code)