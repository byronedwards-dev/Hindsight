from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime


class PredictionsInput(BaseModel):
    """Market prediction inputs (confidence as probability of 'Yes')."""
    above_15pct: float = Field(..., ge=0.0, le=1.0, description="Probability that returns exceed +15%")
    above_10pct: float = Field(..., ge=0.0, le=1.0, description="Probability that returns exceed +10%")
    above_5pct: float = Field(..., ge=0.0, le=1.0, description="Probability that returns exceed +5%")
    above_0pct: float = Field(..., ge=0.0, le=1.0, description="Probability that returns exceed 0%")

    @model_validator(mode='after')
    def validate_monotonic(self):
        """Higher thresholds should have lower or equal probabilities."""
        if not (self.above_15pct <= self.above_10pct <= self.above_5pct <= self.above_0pct):
            raise ValueError(
                "Predictions must be monotonically increasing: "
                "P(>15%) <= P(>10%) <= P(>5%) <= P(>0%)"
            )
        return self


class AllocationInput(BaseModel):
    """Asset allocation inputs (must sum to 100)."""
    stocks: int = Field(..., ge=0, le=100)
    bonds: int = Field(..., ge=0, le=100)
    cash: int = Field(..., ge=0, le=100)
    gold: int = Field(..., ge=0, le=100)

    @model_validator(mode='after')
    def validate_sum(self):
        total = self.stocks + self.bonds + self.cash + self.gold
        if total != 100:
            raise ValueError(f"Allocations must sum to 100, got {total}")
        return self


class GameCreateInput(BaseModel):
    """Input for creating a new game session."""
    scenario_id: int
    predictions: PredictionsInput
    allocation: AllocationInput
    rationale: str = Field(default="", max_length=500)  # Optional, max 500 chars


class GameSessionOut(BaseModel):
    """Output after creating a game session."""
    session_token: str
    scenario_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PredictionResult(BaseModel):
    """Result for a single prediction."""
    threshold: str  # e.g., ">15%"
    user_prediction: str  # "Yes" or "No"
    user_confidence: float  # 0.5-1.0
    actual_outcome: bool
    correct: bool
    brier_contribution: float


class MonthlyDataOut(BaseModel):
    """Monthly data point for charts."""
    month_index: int
    is_forward: bool
    idx_stocks: float
    idx_bonds: float
    idx_cash: float
    idx_gold: float
    gdp_growth_yoy: Optional[float] = None
    unemployment_rate: Optional[float] = None
    inflation_rate_yoy: Optional[float] = None
    fed_funds_rate: Optional[float] = None
    industrial_prod_yoy: Optional[float] = None


class GameRevealOut(BaseModel):
    """Full game results after reveal."""
    session_token: str
    
    # Scenario info
    actual_start_date: str
    actual_period: str
    historical_context: Optional[str] = None
    historical_description: Optional[str] = None  # Longer description
    
    # Full monthly data for charts (36 months)
    monthly_data: List[MonthlyDataOut]
    
    # Prediction results
    prediction_results: List[PredictionResult]
    brier_score: float
    
    # Allocation results
    allocation: AllocationInput
    asset_returns: dict  # {"stocks": 0.15, "bonds": 0.05, ...}
    portfolio_return: float
    portfolio_sharpe: float
    
    # Benchmark comparison
    benchmark_return: float
    benchmark_sharpe: float
    excess_return: float
    excess_sharpe: float
    
    # User's rationale
    rationale: Optional[str] = None


class LeaderboardEntry(BaseModel):
    """Single leaderboard entry."""
    rank: int
    username: str
    games_played: int
    avg_brier_score: float
    avg_sharpe: float
    avg_excess_return: float


class LeaderboardOut(BaseModel):
    """Leaderboard response."""
    entries: List[LeaderboardEntry]
    user_rank: Optional[int] = None
    user_stats: Optional[LeaderboardEntry] = None
