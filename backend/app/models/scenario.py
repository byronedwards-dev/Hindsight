from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Scenario(Base):
    """Pre-computed game scenarios with 36 months of data."""
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    actual_start_date = Column(Date, nullable=False)  # Hidden from user
    display_label = Column(String(50))  # e.g., "Scenario A"
    historical_context = Column(String(200))  # e.g., "Oil Crisis & Stagflation"
    
    # Pre-computed forward returns (real, 12-month)
    fwd_return_stocks = Column(Numeric(8, 4))
    fwd_return_bonds = Column(Numeric(8, 4))
    fwd_return_cash = Column(Numeric(8, 4))
    fwd_return_gold = Column(Numeric(8, 4))
    
    # For Sharpe calculation - annualized volatility
    fwd_volatility_stocks = Column(Numeric(8, 4))
    fwd_volatility_bonds = Column(Numeric(8, 4))
    fwd_volatility_gold = Column(Numeric(8, 4))
    
    # Benchmark returns (60/40 portfolio)
    benchmark_6040_return = Column(Numeric(8, 4))
    benchmark_6040_sharpe = Column(Numeric(8, 4))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    monthly_data = relationship("ScenarioData", back_populates="scenario", order_by="ScenarioData.month_index")
    game_sessions = relationship("GameSession", back_populates="scenario")


class ScenarioData(Base):
    """Monthly data points for each scenario (36 months total)."""
    __tablename__ = "scenario_data"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    month_index = Column(Integer, nullable=False)  # 1-36 (24 history + 12 forward)
    is_forward = Column(Boolean, default=False)  # months 25-36 are forward period
    
    # Indexed values (all start at 100 at month 1)
    idx_stocks = Column(Numeric(10, 4))
    idx_bonds = Column(Numeric(10, 4))
    idx_cash = Column(Numeric(10, 4))
    idx_gold = Column(Numeric(10, 4))
    
    # Macro indicators (actual values, not indexed)
    gdp_growth_yoy = Column(Numeric(6, 2))  # year-over-year %
    unemployment_rate = Column(Numeric(5, 2))
    inflation_rate_yoy = Column(Numeric(6, 2))  # year-over-year CPI change
    fed_funds_rate = Column(Numeric(5, 2))
    industrial_prod_yoy = Column(Numeric(6, 2))
    
    # Relationships
    scenario = relationship("Scenario", back_populates="monthly_data")
    
    __table_args__ = (
        UniqueConstraint('scenario_id', 'month_index', name='unique_scenario_month'),
    )


