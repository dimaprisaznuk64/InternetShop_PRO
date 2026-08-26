from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from app.database import get_db
from app.config import get_settings
from app.utils.security import (
    decode_token,
    verify_token_type,
    verify_token_not_blacklisted,
)
from app.utils.exceptions import ForbiddenError

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class UnauthorizedError(Exception):
    def __init__(self, detail: str = "Could not validate credentials"):
        self.detail = detail
        super().__init__(detail)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.user_repo import get_user_by_id

    try:
        payload = decode_token(token)

        if not verify_token_type(payload, "access"):
            raise UnauthorizedError()

        if not await verify_token_not_blacklisted(payload):
            raise UnauthorizedError("Token has been revoked")

        user_id: str = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError()
    except JWTError:
        raise UnauthorizedError()

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise UnauthorizedError()
    return user


async def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise ForbiddenError("Admin access required")
    return current_user


async def require_manager(current_user=Depends(get_current_user)):
    if current_user.role not in ("admin", "manager"):
        raise ForbiddenError("Manager or admin access required")
    return current_user
