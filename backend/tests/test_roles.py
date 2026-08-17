import pytest
from fastapi import Depends
from app.utils.security import create_access_token, hash_password
from app.database import Base, async_sessionmaker, AsyncSession
from sqlalchemy import insert
from app.models.user import User


@pytest.fixture
async def admin_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="admin-role-id",
        email="admin@test.com",
        username="adminrole",
        hashed_password=hash_password("secret123"),
        role="admin",
    ))
    await db_session.commit()
    return create_access_token("admin-role-id")


@pytest.fixture
async def user_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="user-role-id",
        email="user@test.com",
        username="userrole",
        hashed_password=hash_password("secret123"),
        role="user",
    ))
    await db_session.commit()
    return create_access_token("user-role-id")


@pytest.fixture
async def manager_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="manager-role-id",
        email="manager@test.com",
        username="managerrole",
        hashed_password=hash_password("secret123"),
        role="manager",
    ))
    await db_session.commit()
    return create_access_token("manager-role-id")


@pytest.mark.asyncio
async def test_admin_access(client, admin_token):
    from app.main import app
    from app.utils.dependencies import require_admin

    @app.get("/test-admin-9")
    async def test_endpoint(current_user=Depends(require_admin)):
        return {"role": current_user.role}

    response = await client.get("/test-admin-9", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_user_denied_admin(client, user_token):
    from app.main import app
    from app.utils.dependencies import require_admin

    @app.get("/test-admin-deny-9")
    async def test_endpoint(current_user=Depends(require_admin)):
        return {"role": current_user.role}

    response = await client.get("/test-admin-deny-9", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_manager_access(client, manager_token):
    from app.main import app
    from app.utils.dependencies import require_manager

    @app.get("/test-manager-9")
    async def test_endpoint(current_user=Depends(require_manager)):
        return {"role": current_user.role}

    response = await client.get("/test-manager-9", headers={"Authorization": f"Bearer {manager_token}"})
    assert response.status_code == 200
    assert response.json()["role"] == "manager"


@pytest.mark.asyncio
async def test_user_denied_manager(client, user_token):
    from app.main import app
    from app.utils.dependencies import require_manager

    @app.get("/test-manager-deny-9")
    async def test_endpoint(current_user=Depends(require_manager)):
        return {"role": current_user.role}

    response = await client.get("/test-manager-deny-9", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_no_token_denied(client):
    response = await client.get("/test-admin-9")
    assert response.status_code == 401
