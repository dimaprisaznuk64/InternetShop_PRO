from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.repositories.user_repo import get_user_by_email, get_user_by_id, create_user
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.utils.dependencies import get_current_user
from app.utils.exceptions import AlreadyExistsError, BadRequestError
from app.services.background import email_service, notification_service, task_manager

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise AlreadyExistsError("User with this email already exists")

    hashed = hash_password(data.password)
    user = await create_user(db, data.email, data.username, hashed)

    await task_manager.submit(email_service.send_welcome, data.email, data.username)
    notification_service.create(
        user.id, "welcome", "Welcome!",
        f"Hello {data.username}, welcome to Internet Shop PRO!",
    )

    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise BadRequestError("Invalid email or password")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token: str, db: AsyncSession = Depends(get_db)):
    from jose import JWTError, jwt
    from app.config import get_settings

    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise BadRequestError("Invalid refresh token")
    except JWTError:
        raise BadRequestError("Invalid refresh token")

    user = await get_user_by_id(db, user_id)
    if not user:
        raise BadRequestError("User not found")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return current_user


@router.post("/token", response_model=TokenResponse)
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise BadRequestError("Invalid email or password")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return TokenResponse(access_token=access, refresh_token=refresh)
