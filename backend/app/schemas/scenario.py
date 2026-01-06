from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class ScenarioDataOut(BaseModel):
    """Monthly data point for a scenario."""
    month_index: int
    is_forward: bool
    
    # Indexed values
    idx_stocks: float
    idx_bonds: float
    idx_cash: float
    idx_gold: float
    
    # Macro indicators
    gdp_growth_yoy: Optional[float] = None
    unemployment_rate: Optional[float] = None
    inflation_rate_yoy: Optional[float] = None
    fed_funds_rate: Optional[float] = None
    industrial_prod_yoy: Optional[float] = None

    class Config:
        from_attributes = True


class ScenarioBase(BaseModel):
    """Base scenario info."""
    id: int
    display_label: Optional[str] = None

    class Config:
        from_attributes = True


class ScenarioOut(ScenarioBase):
    """Full scenario output (for admin/debug)."""
    actual_start_date: date
    historical_context: Optional[str] = None
    fwd_return_stocks: float
    fwd_return_bonds: float
    fwd_return_cash: float
    fwd_return_gold: float


class ScenarioHistoryOut(BaseModel):
    """Historical data output (24 months, dates obscured)."""
    scenario_id: int
    display_label: Optional[str] = None
    monthly_data: List[ScenarioDataOut]


class ScenarioRevealOut(BaseModel):
    """Full scenario data including forward period and actual dates."""
    scenario_id: int
    display_label: Optional[str] = None
    actual_start_date: date
    actual_period: str  # e.g., "January 1973 - January 1976"
    historical_context: Optional[str] = None
    
    # Forward returns
    fwd_return_stocks: float
    fwd_return_bonds: float
    fwd_return_cash: float
    fwd_return_gold: float
    
    # Benchmark
    benchmark_6040_return: float
    benchmark_6040_sharpe: float
    
    # All monthly data including forward period
    monthly_data: List[ScenarioDataOut]


