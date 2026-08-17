import pytest
from app.utils.security import create_access_token, hash_password
from app.database import AsyncSession
from sqlalchemy import insert
from app.models.user import User


async def _admin_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="admin-cat-id",
        email="admincat@test.com",
        username="admincat",
        hashed_password=hash_password("secret123"),
        role="admin",
    ))
    await db_session.commit()
    return create_access_token("admin-cat-id")


async def _user_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="user-cat-id",
        email="usercat@test.com",
        username="usercat",
        hashed_password=hash_password("secret123"),
        role="user",
    ))
    await db_session.commit()
    return create_access_token("user-cat-id")


@pytest.mark.asyncio
async def test_list_categories_empty(client):
    response = await client.get("/api/categories/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_category(client, db_session):
    token = await _admin_token(db_session)
    response = await client.post(
        "/api/categories/",
        json={"name": "Electronics", "slug": "electronics"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Electronics"
    assert data["slug"] == "electronics"


@pytest.mark.asyncio
async def test_create_category_user_denied(client, db_session):
    token = await _user_token(db_session)
    response = await client.post(
        "/api/categories/",
        json={"name": "Test", "slug": "test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_category_duplicate_slug(client, db_session):
    token = await _admin_token(db_session)
    await client.post(
        "/api/categories/",
        json={"name": "Books", "slug": "books"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.post(
        "/api/categories/",
        json={"name": "Books 2", "slug": "books"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_category(client, db_session):
    token = await _admin_token(db_session)
    create_resp = await client.post(
        "/api/categories/",
        json={"name": "Phones", "slug": "phones"},
        headers={"Authorization": f"Bearer {token}"},
    )
    cat_id = create_resp.json()["id"]

    response = await client.get(f"/api/categories/{cat_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Phones"


@pytest.mark.asyncio
async def test_get_category_not_found(client):
    response = await client.get("/api/categories/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_category(client, db_session):
    token = await _admin_token(db_session)
    create_resp = await client.post(
        "/api/categories/",
        json={"name": "Old", "slug": "old"},
        headers={"Authorization": f"Bearer {token}"},
    )
    cat_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/categories/{cat_id}",
        json={"name": "New", "slug": "new"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New"


@pytest.mark.asyncio
async def test_delete_category(client, db_session):
    token = await _admin_token(db_session)
    create_resp = await client.post(
        "/api/categories/",
        json={"name": "ToDelete", "slug": "to-delete"},
        headers={"Authorization": f"Bearer {token}"},
    )
    cat_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/categories/{cat_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    get_resp = await client.get(f"/api/categories/{cat_id}")
    assert get_resp.status_code == 404
