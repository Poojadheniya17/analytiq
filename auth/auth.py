# auth/auth.py
import hashlib
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.models import User, Client
from database.connection import SessionLocal

DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "users")
)


def utcnow():
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _validate_signup(username: str, email: str, password: str):
    username = username.strip()
    email    = email.strip().lower()

    if len(username) < 3:
        return False, "Username must be at least 3 characters.", None, None
    if len(username) > 30:
        return False, "Username too long (max 30 characters).", None, None
    if not all(c.isalnum() or c in "_-" for c in username):
        return False, "Username can only contain letters, numbers, _ and -", None, None
    if len(password) < 6:
        return False, "Password must be at least 6 characters.", None, None
    if "@" not in email or "." not in email:
        return False, "Enter a valid email address.", None, None

    return True, "", username, email


def signup(username: str, email: str, password: str) -> tuple[bool, str]:
    valid, msg, username, email = _validate_signup(username, email, password)
    if not valid:
        return False, msg

    db: Session = SessionLocal()
    try:
        if db.query(User).filter(User.username.ilike(username)).first():
            return False, "Username already taken. Please choose another."
        if db.query(User).filter(User.email.ilike(email)).first():
            return False, "An account with this email already exists. Try signing in."

        user = User(
            username = username.lower(),
            email    = email,
            password = hash_password(password),
            created  = utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        os.makedirs(os.path.join(DATA_DIR, str(user.id)), exist_ok=True)
        return True, "Account created! You can now sign in."

    except IntegrityError:
        db.rollback()
        return False, "Username or email already exists."
    except Exception as e:
        db.rollback()
        return False, f"Signup failed: {str(e)}"
    finally:
        db.close()


def login(username: str, password: str) -> tuple[bool, str, dict]:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(
            User.username.ilike(username.strip()),
            User.password == hash_password(password)
        ).first()

        if user:
            return True, "Login successful!", user.to_dict()
        return False, "Incorrect username or password.", {}

    except Exception as e:
        return False, f"Login failed: {str(e)}", {}
    finally:
        db.close()


def get_clients(user_id: int) -> list:
    db: Session = SessionLocal()
    try:
        clients = db.query(Client).filter(
            Client.user_id == user_id
        ).order_by(Client.created.desc()).all()
        return [c.to_dict() for c in clients]
    except Exception:
        return []
    finally:
        db.close()


def add_client(user_id: int, name: str, domain: str) -> tuple[bool, str]:
    name = name.strip()
    if len(name) < 2:
        return False, "Client name must be at least 2 characters."
    if len(name) > 50:
        return False, "Client name too long (max 50 characters)."

    db: Session = SessionLocal()
    try:
        client = Client(
            user_id = user_id,
            name    = name,
            domain  = domain,
            created = utcnow()
        )
        db.add(client)
        db.commit()
        db.refresh(client)

        safe_name  = name.lower().replace(" ", "_")
        client_dir = os.path.join(DATA_DIR, str(user_id), safe_name)
        os.makedirs(client_dir, exist_ok=True)
        return True, f"Client '{name}' created."

    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


def delete_client(client_id: int, user_id: int) -> tuple[bool, str]:
    db: Session = SessionLocal()
    try:
        client = db.query(Client).filter(
            Client.id == client_id,
            Client.user_id == user_id
        ).first()
        if not client:
            return False, "Client not found."
        db.delete(client)
        db.commit()
        return True, "Client deleted."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()
