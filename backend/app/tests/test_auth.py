from __future__ import annotations


def test_register_login_and_me(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Alex Product",
            "email": "alex@example.com",
            "password": "StrongPass123!",
        },
    )
    assert register_response.status_code == 200
    register_payload = register_response.json()
    assert register_payload["user"]["email"] == "alex@example.com"
    assert register_payload["access_token"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "alex@example.com",
            "password": "StrongPass123!",
        },
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["user"]["full_name"] == "Alex Product"

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_payload['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "alex@example.com"
