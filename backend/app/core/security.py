from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
import random
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    print(f"[Security] Created JWT token for subject={subject}, expires={expire.isoformat()}")
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    import logging
    logger = logging.getLogger(__name__)
    char_len = len(plain_password) if plain_password else 0
    byte_len = len(plain_password.encode("utf-8")) if plain_password else 0
    logger.info(f"[Security] verify_password: plain_password char_len={char_len}, byte_len={byte_len}")
    logger.info(f"[Security] verify_password: plain_password={repr(plain_password)}, hashed_password={repr(hashed_password)}")
    if byte_len > 72:
        logger.warning("[Security] verify_password: password exceeds 72 bytes, failing verification.")
        return False
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    import logging
    logger = logging.getLogger(__name__)
    pwd_type = type(password)
    pwd_len = len(password) if password else 0
    pwd_bytes_len = len(password.encode("utf-8")) if password else 0
    logger.info(f"[Security] get_password_hash: type(password)={pwd_type}, password={repr(password)}, len={pwd_len}, bytes_len={pwd_bytes_len}")
    if pwd_bytes_len > 72:
        raise ValueError("Password cannot be longer than 72 bytes")
    return pwd_context.hash(password)

def generate_otp() -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(6)])
