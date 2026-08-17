import pytest


async def _register_and_login(client):
    await client.post("/api/auth/register", json={
        "email": "profile@example.com",
        "username": "profileuser",
        "password": "secret123",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "profile@example.com",
        "password": "secret123",
    })
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_get_profile(client):
    token = await _register_and_login(client)
    response = await client.get("/api/profile/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile@example.com"
    assert data["username"] == "profileuser"


@pytest.mark.asyncio
async def test_update_profile(client):
    token = await _register_and_login(client)
    response = await client.put(
        "/api/profile/",
        json={"username": "newname", "email": "new@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newname"
    assert data["email"] == "new@example.com"


@pytest.mark.asyncio
async def test_change_password(client):
    token = await _register_and_login(client)
    response = await client.put(
        "/api/profile/password",
        json={"current_password": "secret123", "new_password": "newsecret456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    login_resp = await client.post("/api/auth/login", json={
        "email": "profile@example.com",
        "password": "newsecret456",
    })
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client):
    token = await _register_and_login(client)
    response = await client.put(
        "/api/profile/password",
        json={"current_password": "wrongpass", "new_password": "newsecret456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_profile(client):
    token = await _register_and_login(client)
    response = await client.delete("/api/profile/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    me_resp = await client.get("/api/profile/", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_no_token(client):
    response = await client.get("/api/profile/")
    assert response.status_code == 401
