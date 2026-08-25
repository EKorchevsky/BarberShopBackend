from datetime import datetime, timedelta, timezone
from typing import Optional

from authlib.jose import jwt
from authlib.jose.errors import JoseError

from config import settings

REVIEW_COOKIE_NAME = "reviewable_barbers"
REVIEW_COOKIE_MAX_AGE = 180 * 24 * 60 * 60  # 180 days


def _decode_barber_ids(token: Optional[str]) -> list[int]:
    if not token:
        return []
    try:
        claims = jwt.decode(token, settings.SECRET_KEY)
        claims.validate()
        return [int(barber_id) for barber_id in claims.get("barbers", [])]
    except JoseError:
        return []


def add_barber_to_cookie(existing_token: Optional[str], barber_id: int) -> str:
    barber_ids = set(_decode_barber_ids(existing_token))
    barber_ids.add(barber_id)

    now = datetime.now(timezone.utc)
    payload = {
        "barbers": sorted(barber_ids),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=REVIEW_COOKIE_MAX_AGE)).timestamp()),
    }
    header = {"alg": settings.ALGORITHM}
    token = jwt.encode(header, payload, settings.SECRET_KEY)
    return token.decode("utf-8") if isinstance(token, bytes) else token


def can_review_barber(token: Optional[str], barber_id: int) -> bool:
    return barber_id in _decode_barber_ids(token)
