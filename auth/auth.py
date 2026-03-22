# ============================================================
# auth/auth.py
# Analytiq — Login, Signup, Session Management
# ============================================================

import sqlite3
import hashlib
import os
import streamlit as st
from datetime import datetime

DB_PATH = "analytiq.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create users and sessions tables if they don't exist."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT UNIQUE NOT NULL,
            email     TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            created   TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            name       TEXT NOT NULL,
            domain     TEXT,
            created    TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def signup(username: str, email: str, password: str) -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if "@" not in email:
        return False, "Enter a valid email address."

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, email, password, created) VALUES (?, ?, ?, ?)",
            (username.lower(), email.lower(), hash_password(password), datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

        # Create user data folder
        os.makedirs(f"data/users/{username.lower()}", exist_ok=True)
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username or email already exists."


def login(username: str, password: str) -> tuple[bool, str, dict]:
    """Login user. Returns (success, message, user_data)."""
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username.lower(), hash_password(password))
    ).fetchone()
    conn.close()

    if user:
        return True, "Login successful!", dict(user)
    return False, "Invalid username or password.", {}


def get_clients(user_id: int) -> list:
    """Get all clients for a user."""
    conn = get_db()
    clients = conn.execute(
        "SELECT * FROM clients WHERE user_id = ? ORDER BY created DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(c) for c in clients]


def add_client(user_id: int, name: str, domain: str) -> tuple[bool, str]:
    """Add a new client workspace."""
    if len(name) < 2:
        return False, "Client name too short."
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO clients (user_id, name, domain, created) VALUES (?, ?, ?, ?)",
            (user_id, name, domain, datetime.now().isoformat())
        )
        conn.commit()
        client_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        # Create client data folder
        safe_name = name.lower().replace(" ", "_")
        os.makedirs(f"data/users/{user_id}/{safe_name}", exist_ok=True)
        return True, f"Client '{name}' created."
    except Exception as e:
        return False, str(e)


def delete_client(client_id: int, user_id: int) -> tuple[bool, str]:
    """Delete a client and their data."""
    try:
        conn = get_db()
        conn.execute(
            "DELETE FROM clients WHERE id = ? AND user_id = ?",
            (client_id, user_id)
        )
        conn.commit()
        conn.close()
        return True, "Client deleted."
    except Exception as e:
        return False, str(e)


def require_login():
    """
    Call this at the top of every page.
    Redirects to login if not authenticated.
    Returns user dict if logged in.
    """
    if "user" not in st.session_state or not st.session_state.user:
        st.error("Please log in to access this page.")
        st.stop()
    return st.session_state.user
