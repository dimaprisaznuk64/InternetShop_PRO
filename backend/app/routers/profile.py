from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate, PasswordChange
from app.utils.dependencies import get_current_user
from app.utils.security import hash_password, verify_password
from app.utils.exceptions import BadRequestError
from app.repositories.user_repo import get_user_by_id

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/", response_model=UserResponse)
async def get_profile(current_user=Depends(get_current_user)):
    return current_user


@router.put("/", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.username = data.username
    current_user.email = data.email
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: PasswordChange,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise BadRequestError("Current password is incorrect")
    current_user.hashed_password = hash_password(data.new_password)
    await db.commit()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.delete(current_user)
    await db.commit()
