from sqlalchemy import Column, Integer, String, Numeric, Text, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class GameSession(Base):
    """User game sessions with predictions, allocations, and scores."""
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Optional, linked when authenticated
    session_token = Column(String(64), unique=True, index=True, nullable=False)
    username = Column(String(50), index=True)  # Optional, for leaderboard
    
    # Market predictions (confidence 0.50 - 1.00, stored as probability of "Yes")
    pred_above_15pct = Column(Numeric(4, 3))
    pred_above_10pct = Column(Numeric(4, 3))
    pred_above_5pct = Column(Numeric(4, 3))
    pred_above_0pct = Column(Numeric(4, 3))
    
    # Asset allocation (must sum to 100)
    alloc_stocks = Column(Integer)
    alloc_bonds = Column(Integer)
    alloc_cash = Column(Integer)
    alloc_gold = Column(Integer)
    
    # Written rationale
    rationale = Column(Text)
    
    # Computed scores (filled after reveal)
    brier_score = Column(Numeric(6, 4))
    portfolio_return = Column(Numeric(8, 4))
    portfolio_sharpe = Column(Numeric(6, 4))
    vs_benchmark_return = Column(Numeric(8, 4))  # portfolio return - benchmark return
    vs_benchmark_sharpe = Column(Numeric(6, 4))
    
    # Optional reflection after reveal
    reflection = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    scenario = relationship("Scenario", back_populates="game_sessions")
    user = relationship("User", back_populates="game_sessions")
    
    __table_args__ = (
        CheckConstraint('alloc_stocks >= 0 AND alloc_stocks <= 100', name='check_alloc_stocks'),
        CheckConstraint('alloc_bonds >= 0 AND alloc_bonds <= 100', name='check_alloc_bonds'),
        CheckConstraint('alloc_cash >= 0 AND alloc_cash <= 100', name='check_alloc_cash'),
        CheckConstraint('alloc_gold >= 0 AND alloc_gold <= 100', name='check_alloc_gold'),
    )


