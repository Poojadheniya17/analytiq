# database/migrate.py
# Analytiq — Run this to initialise DB and migrate existing SQLite data
# Usage: python database/migrate.py

import os
import sys
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

from database.connection import engine, init_db
from database.models import Base
from sqlalchemy.orm import Session
from sqlalchemy import text

SQLITE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "analytiq.db")
)


def migrate():
    print("=" * 50)
    print("Analytiq — Database Migration")
    print("=" * 50)

    # Step 1: Create new tables (adds is_active and analyses table)
    print("Step 1: Creating / updating tables...")
    Base.metadata.create_all(bind=engine)
    print("        Done.")

    # Step 2: Add is_active column to existing SQLite if missing
    # This fixes the "no such column: users.is_active" error
    print("Step 2: Patching existing SQLite schema...")
    if os.path.exists(SQLITE_PATH):
        sqlite_conn = sqlite3.connect(SQLITE_PATH)
        try:
            sqlite_conn.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
            sqlite_conn.commit()
            print("        Added is_active column to users table.")
        except sqlite3.OperationalError:
            print("        is_active column already exists — skipping.")
        sqlite_conn.close()

    # Step 3: Read from SQLite
    print("Step 3: Reading data from SQLite...")
    if not os.path.exists(SQLITE_PATH):
        print("        No SQLite database found. Starting fresh.")
        return

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row

    users   = sqlite_conn.execute("SELECT * FROM users").fetchall()
    clients = sqlite_conn.execute("SELECT * FROM clients").fetchall()
    sqlite_conn.close()

    print(f"        Found {len(users)} users, {len(clients)} clients.")

    # Step 4: Write to target DB (SQLite or PostgreSQL)
    print("Step 4: Writing to database...")
    with Session(engine) as db:
        for u in users:
            existing = db.execute(
                text("SELECT id FROM users WHERE username = :u"),
                {"u": u["username"]}
            ).fetchone()
            if not existing:
                db.execute(text("""
                    INSERT INTO users (id, username, email, password, is_active, created)
                    VALUES (:id, :username, :email, :password, :is_active, :created)
                """), {
                    "id":        u["id"],
                    "username":  u["username"],
                    "email":     u["email"],
                    "password":  u["password"],
                    "is_active": 1,
                    "created":   u["created"],
                })
        db.commit()

        for c in clients:
            existing = db.execute(
                text("SELECT id FROM clients WHERE id = :id"),
                {"id": c["id"]}
            ).fetchone()
            if not existing:
                db.execute(text("""
                    INSERT INTO clients (id, user_id, name, domain, created)
                    VALUES (:id, :user_id, :name, :domain, :created)
                """), {
                    "id":      c["id"],
                    "user_id": c["user_id"],
                    "name":    c["name"],
                    "domain":  c["domain"],
                    "created": c["created"],
                })
        db.commit()

    print(f"        Migrated {len(users)} users and {len(clients)} clients.")
    print()
    print("Migration complete!")
    print()
    print("Next step: run the backend and verify /health returns 'connected'")


if __name__ == "__main__":
    migrate()
