from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, index=True)
    home_country = Column(String(80), nullable=True)
    home_city = Column(String(80), nullable=True)
    trust_score = Column(Integer, nullable=False, default=70)
    average_transaction_amount = Column(Float, nullable=False, default=0.0)
    account_number = Column(String(64), nullable=True, unique=True, index=True)
    balance = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    login_events = relationship(
        "LoginEvent", back_populates="user", cascade="all, delete-orphan"
    )
    transactions = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    security_logs = relationship("SecurityLog", back_populates="user")
    fraud_alerts = relationship("FraudAlert", back_populates="user")
    trust_score_history = relationship(
        "TrustScoreHistory", back_populates="user", cascade="all, delete-orphan"
    )
    bank_messages = relationship("BankMessage", back_populates="user")
    message_verification_checks = relationship(
        "MessageVerificationCheck",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    analyst_notes = relationship("AnalystNote", back_populates="analyst")
