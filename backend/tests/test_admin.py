import pytest
from app.utils.security import create_access_token, hash_password
from app.database import AsyncSession
from sqlalchemy import insert
from app.models.user import User


async def _admin_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="adm-panel-id", email="admpanel@test.com", username="admpanel",
        hashed_password=hash_password("secret123"), role="admin",
    ))
    await db_session.commit()
    return create_access_token("adm-panel-id")


async def _user_in_db(db_session: AsyncSession, uid, email, username, role="user"):
    await db_session.execute(insert(User).values(
        id=uid, email=email, username=username,
        hashed_password=hash_password("secret123"), role=role,
    ))
    await db_session.commit()


@pytest.mark.asyncio
async def test_list_users(client, db_session):
    token = await _admin_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    await _user_in_db(db_session, "u1", "u1@test.com", "user1")
    await _user_in_db(db_session, "u2", "u2@test.com", "user2")

    resp = await client.get("/api/admin/users", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 2


@pytest.mark.asyncio
async def test_search_users(client, db_session):
    token = await _admin_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    await _user_in_db(db_session, "u3", "searchme@test.com", "searchable")

    resp = await client.get("/api/admin/users?q=searchme", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_block_user(client, db_session):
    token = await _admin_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    await _user_in_db(db_session, "u4", "block@test.com", "blockme")

    resp = await client.patch("/api/admin/users/u4/block", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_unblock_user(client, db_session):
    token = await _admin_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    await _user_in_db(db_session, "u5", "unblock@test.com", "unblockme")

    await client.patch("/api/admin/users/u5/block", headers=headers)
    resp = await client.patch("/api/admin/users/u5/unblock", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


@pytest.mark.asyncio
async def test_admin_cannot_block_self(client, db_session):
    token = await _admin_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.patch("/api/admin/users/adm-panel-id/block", headers=headers)
    assert resp.status_code == 400



@pytest.mark.asyncio
async def test_change_role(client, db_session):
    token = await _admin_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    await _user_in_db(db_session, "u6", "role@test.com", "roleuser")

    resp = await client.patch("/api/admin/users/u6/role?role=manager", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "manager"


@pytest.mark.asyncio
async def test_invalid_role(client, db_session):
    token = await _admin_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    await _user_in_db(db_session, "u7", "badrole@test.com", "badrole")

    resp = await client.patch("/api/admin/users/u7/role?role=superadmin", headers=headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_stats(client, db_session):
    token = await _admin_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/admin/stats", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_users" in data
    assert "total_revenue" in data
    assert "average_rating" in data


@pytest.mark.asyncio
async def test_user_cannot_access_admin(client, db_session):
    await _user_in_db(db_session, "u8", "noadmin@test.com", "noadmin")
    token = create_access_token("u8")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/admin/users", headers=headers)
    assert resp.status_code == 403
