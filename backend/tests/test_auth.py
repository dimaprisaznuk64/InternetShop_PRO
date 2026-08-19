import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "secret123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/api/auth/register", json={
        "email": "dup@example.com",
        "username": "user1",
        "password": "secret123",
    })
    response = await client.post("/api/auth/register", json={
        "email": "dup@example.com",
        "username": "user2",
        "password": "secret123",
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    response = await client.post("/api/auth/register", json={
        "email": "not-an-email",
        "username": "testuser",
        "password": "secret123",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client):
    response = await client.post("/api/auth/register", json={
        "email": "short@example.com",
        "username": "testuser",
        "password": "12",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_username(client):
    response = await client.post("/api/auth/register", json={
        "email": "user@example.com",
        "username": "ab",
        "password": "secret123",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/auth/register", json={
        "email": "login@example.com",
        "username": "loginuser",
        "password": "mypassword",
    })
    response = await client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "mypassword",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "email": "wrong@example.com",
        "username": "wronguser",
        "password": "correct",
    })
    response = await client.post("/api/auth/login", json={
        "email": "wrong@example.com",
        "password": "incorrect",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "whatever",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_me(client):
    await client.post("/api/auth/register", json={
        "email": "me@example.com",
        "username": "meuser",
        "password": "secret123",
    })
    login_resp = await client.post("/api/auth/login", json={
        "email": "me@example.com",
        "password": "secret123",
    })
    token = login_resp.json()["access_token"]

    response = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["username"] == "meuser"


@pytest.mark.asyncio
async def test_get_me_no_token(client):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    await client.post("/api/auth/register", json={
        "email": "refresh@example.com",
        "username": "refreshuser",
        "password": "secret123",
    })
    login_resp = await client.post("/api/auth/login", json={
        "email": "refresh@example.com",
        "password": "secret123",
    })
    refresh = login_resp.json()["refresh_token"]

    response = await client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    response = await client.post("/api/auth/refresh", json={"refresh_token": "invalidtoken123"})
    assert response.status_code == 400
