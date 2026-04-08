# tests/test_api.py
# Analytiq — API integration tests

import pytest


class TestAuthEndpoints:

    def test_signup_endpoint(self, client):
        res = client.post("/api/auth/signup", json={
            "username": "apiuser1",
            "email":    "apiuser1@test.com",
            "password": "password123"
        })
        assert res.status_code == 200
        assert "message" in res.json()

    def test_signup_duplicate_returns_400(self, client):
        client.post("/api/auth/signup", json={
            "username": "dupapi",
            "email":    "dupapi@test.com",
            "password": "password123"
        })
        res = client.post("/api/auth/signup", json={
            "username": "dupapi",
            "email":    "dupapi2@test.com",
            "password": "password123"
        })
        assert res.status_code == 400

    def test_login_endpoint_success(self, client):
        client.post("/api/auth/signup", json={
            "username": "loginapi",
            "email":    "loginapi@test.com",
            "password": "password123"
        })
        res = client.post("/api/auth/login", json={
            "username": "loginapi",
            "password": "password123"
        })
        assert res.status_code == 200
        data = res.json()
        assert "user" in data
        assert data["user"]["username"] == "loginapi"

    def test_login_wrong_password_returns_401(self, client):
        client.post("/api/auth/signup", json={
            "username": "wrongpassapi",
            "email":    "wrongpassapi@test.com",
            "password": "correctpass"
        })
        res = client.post("/api/auth/login", json={
            "username": "wrongpassapi",
            "password": "wrongpass"
        })
        assert res.status_code == 401

    def test_logout_endpoint(self, client):
        res = client.post("/api/auth/logout")
        assert res.status_code == 200

    def test_me_endpoint_unauthenticated(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 401


class TestHealthEndpoint:

    def test_health_returns_ok(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_root_returns_status(self, client):
        res = client.get("/")
        assert res.status_code == 200


class TestClientEndpoints:

    def test_create_client(self, client, test_user):
        res = client.post("/api/clients/", json={
            "user_id": test_user["id"],
            "name":    "Test Corp",
            "domain":  "Finance"
        })
        assert res.status_code == 200

    def test_get_clients(self, client, test_user):
        res = client.get(f"/api/clients/{test_user['id']}")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_create_client_short_name(self, client, test_user):
        res = client.post("/api/clients/", json={
            "user_id": test_user["id"],
            "name":    "A",
            "domain":  "Finance"
        })
        assert res.status_code == 400
