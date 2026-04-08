# database/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship  # SQLAlchemy 2.0 import
from datetime import datetime, timezone

Base = declarative_base()


def utcnow():
    """Timezone-aware UTC datetime — replaces deprecated datetime.utcnow()"""
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id        = Column(Integer, primary_key=True, index=True)
    username  = Column(String(30), unique=True, nullable=False, index=True)
    email     = Column(String(255), unique=True, nullable=False, index=True)
    password  = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created   = Column(DateTime, default=utcnow)

    clients   = relationship("Client", back_populates="user", cascade="all, delete")

    def to_dict(self):
        return {
            "id":       self.id,
            "username": self.username,
            "email":    self.email,
            "created":  self.created.isoformat() if self.created else None,
        }


class Client(Base):
    __tablename__ = "clients"

    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name      = Column(String(50), nullable=False)
    domain    = Column(String(100))
    created   = Column(DateTime, default=utcnow)

    user      = relationship("User", back_populates="clients")
    analyses  = relationship("Analysis", back_populates="client", cascade="all, delete")

    def to_dict(self):
        return {
            "id":      self.id,
            "user_id": self.user_id,
            "name":    self.name,
            "domain":  self.domain,
            "created": self.created.isoformat() if self.created else None,
        }


class Analysis(Base):
    __tablename__ = "analyses"

    id            = Column(Integer, primary_key=True, index=True)
    client_id     = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    user_id       = Column(Integer, nullable=False)
    type          = Column(String(50))
    status        = Column(String(20), default="pending")
    result_path   = Column(Text)
    error_message = Column(Text)
    created       = Column(DateTime, default=utcnow)
    completed     = Column(DateTime)

    client        = relationship("Client", back_populates="analyses")

    def to_dict(self):
        return {
            "id":        self.id,
            "client_id": self.client_id,
            "type":      self.type,
            "status":    self.status,
            "created":   self.created.isoformat() if self.created else None,
            "completed": self.completed.isoformat() if self.completed else None,
        }
