# tests/test_auth.py
# Analytiq — Auth unit and integration tests

import pytest
from auth.auth import signup, login, hash_password


class TestSignup:

    def test_signup_success(self):
        success, msg = signup("newuser1", "newuser1@test.com", "password123")
        assert success is True
        assert "created" in msg.lower()

    def test_signup_duplicate_username(self):
        signup("dupuser", "dup1@test.com", "password123")
        success, msg = signup("dupuser", "dup2@test.com", "password123")
        assert success is False
        assert "taken" in msg.lower() or "exists" in msg.lower()

    def test_signup_duplicate_email(self):
        signup("emailuser1", "same@test.com", "password123")
        success, msg = signup("emailuser2", "same@test.com", "password123")
        assert success is False
        assert "email" in msg.lower()

    def test_signup_short_username(self):
        success, msg = signup("ab", "ab@test.com", "password123")
        assert success is False
        assert "3 characters" in msg

    def test_signup_short_password(self):
        success, msg = signup("validuser", "valid@test.com", "abc")
        assert success is False
        assert "6 characters" in msg

    def test_signup_invalid_email(self):
        success, msg = signup("validuser2", "notanemail", "password123")
        assert success is False
        assert "email" in msg.lower()

    def test_signup_special_chars_username(self):
        success, msg = signup("user@name!", "special@test.com", "password123")
        assert success is False

    def test_signup_username_with_underscore(self):
        success, msg = signup("user_name", "underscore@test.com", "password123")
        assert success is True

    def test_signup_strips_whitespace(self):
        success, msg = signup("  spaceuser  ", "space@test.com", "password123")
        assert success is True


class TestLogin:

    def test_login_success(self):
        signup("loginuser", "login@test.com", "mypassword")
        success, msg, user = login("loginuser", "mypassword")
        assert success is True
        assert user["username"] == "loginuser"
        assert "password" not in user  # password never returned

    def test_login_wrong_password(self):
        signup("wrongpass", "wrongpass@test.com", "correctpass")
        success, msg, user = login("wrongpass", "wrongpass")
        assert success is False
        assert user == {}

    def test_login_nonexistent_user(self):
        success, msg, user = login("doesnotexist", "anypassword")
        assert success is False

    def test_login_case_insensitive_username(self):
        signup("caseuser", "case@test.com", "password123")
        success, msg, user = login("CASEUSER", "password123")
        assert success is True

    def test_password_not_in_response(self):
        signup("safeuser", "safe@test.com", "password123")
        _, _, user = login("safeuser", "password123")
        assert "password" not in user


class TestHashPassword:

    def test_hash_is_deterministic(self):
        assert hash_password("hello") == hash_password("hello")

    def test_different_passwords_different_hashes(self):
        assert hash_password("hello") != hash_password("world")

    def test_hash_is_string(self):
        result = hash_password("test")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex = 64 chars
