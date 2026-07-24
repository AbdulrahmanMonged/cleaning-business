from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import get_settings

password_hash = PasswordHash((Argon2Hasher(), BcryptHasher()))


def create_access_token(subject: str, expire_delta: timedelta):
    settings = get_settings()
    expire = datetime.now(timezone.utc) + expire_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, settings.JWT_ALGORITHM)
    return encoded_jwt


def get_password_hash(plain_password: str):
    return password_hash.hash(password=plain_password)


def verify_password(plain_password: str, hashed_password: str):
    return password_hash.verify_and_update(plain_password, hashed_password)
