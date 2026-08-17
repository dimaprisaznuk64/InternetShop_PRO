from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.repositories.user_repo import get_user_by_email, create_user
from app.utils.security import hash_password, create_access_token, create_refresh_token
from app.utils.exceptions import AlreadyExistsError

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise AlreadyExistsError("User with this email already exists")

    hashed = hash_password(data.password)
    user = await create_user(db, data.email, data.username, hashed)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    from app.utils.security import verify_password
    from app.utils.exceptions import BadRequestError

    user = await get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise BadRequestError("Invalid email or password")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return TokenResponse(access_token=access, refresh_token=refresh)
