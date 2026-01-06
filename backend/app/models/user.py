"""User model for authentication."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User model for magic link authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    
    # Auth tokens
    magic_link_token = Column(String(255), nullable=True)
    magic_link_expires = Column(DateTime, nullable=True)
    
    # Session management
    session_token = Column(String(255), nullable=True, index=True)
    session_expires = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Stats (cached for quick access)
    games_played = Column(Integer, default=0)
    avg_brier_score = Column(Integer, nullable=True)  # Stored as int * 10000 for precision
    avg_portfolio_return = Column(Integer, nullable=True)  # Stored as int * 10000
    wins_vs_benchmark = Column(Integer, default=0)
    losses_vs_benchmark = Column(Integer, default=0)
    
    # Relationships
    game_sessions = relationship("GameSession", back_populates="user")


class MagicLinkAttempt(Base):
    """Track magic link attempts for rate limiting."""
    __tablename__ = "magic_link_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    attempted_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(50), nullable=True)

