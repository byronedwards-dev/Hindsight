"""
Compute game scenarios from normalized data.

This script:
1. Loads normalized data
2. For each start date:
   - Extracts 36-month window (24 history + 12 forward)
   - Indexes all series to 100 at month 1
   - Calculates forward returns, volatilities, Sharpe ratios
   - Stores scenario in database

Usage:
    python compute_scenarios.py [--start-dates dates.json]
"""
import sys
import json
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import Scenario, ScenarioData
from app.database import Base

DATA_DIR = Path(__file__).parent.parent / "data"

# Default curated start dates for interesting economic periods
DEFAULT_START_DATES = [
    # Oil Crisis
    "1973-01-01",
    # Volcker Era
    "1980-01-01",
    "1982-01-01",
    # 1987 Crash
    "1987-06-01",
    # Early 90s Recession
    "1990-06-01",
    # Dot-com Bubble
    "1998-01-01",
    "2000-01-01",
    # Post Dot-com
    "2002-06-01",
    # Pre-GFC
    "2006-01-01",
    "2007-06-01",
    # GFC
    "2008-06-01",
    # Recovery
    "2010-01-01",
    "2012-01-01",
    # Recent
    "2016-01-01",
    "2018-01-01",
    "2020-01-01",
]

# Historical context for each period
HISTORICAL_CONTEXT = {
    "1973-01-01": "Oil Crisis & Stagflation",
    "1980-01-01": "Volcker Shock - Peak Interest Rates",
    "1982-01-01": "Early 80s Recession",
    "1987-06-01": "Pre-Black Monday",
    "1990-06-01": "Gulf War Recession",
    "1998-01-01": "Asian Financial Crisis & LTCM",
    "2000-01-01": "Dot-com Peak",
    "2002-06-01": "Post Dot-com Recovery",
    "2006-01-01": "Housing Boom Peak",
    "2007-06-01": "Pre-Financial Crisis",
    "2008-06-01": "Global Financial Crisis",
    "2010-01-01": "Post-GFC Recovery",
    "2012-01-01": "European Debt Crisis",
    "2016-01-01": "Post-Oil Crash",
    "2018-01-01": "Late Cycle Expansion",
    "2020-01-01": "Pre-COVID Peak",
}


def load_normalized_data() -> pd.DataFrame:
    """Load normalized data from parquet."""
    path = DATA_DIR / "normalized_data.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Normalized data not found at {path}. Run normalize_data.py first.")
    
    return pd.read_parquet(path)


def extract_scenario_window(
    df: pd.DataFrame,
    start_date: pd.Timestamp,
    lookback_months: int = 24,
    forward_months: int = 12
) -> Optional[pd.DataFrame]:
    """
    Extract a scenario window centered on start_date.
    
    The window starts (lookback_months) before start_date and extends
    (forward_months) after start_date, for a total of (lookback + forward) months.
    
    Note: start_date refers to month 24 (end of lookback period).
    """
    # Calculate window bounds
    window_start = start_date - pd.DateOffset(months=lookback_months)
    window_end = start_date + pd.DateOffset(months=forward_months - 1)
    
    # Extract window
    window = df[(df.index >= window_start) & (df.index <= window_end)].copy()
    
    # Verify we have enough data
    expected_months = lookback_months + forward_months
    if len(window) < expected_months - 1:  # Allow 1 month tolerance
        print(f"  Warning: Insufficient data for {start_date}. Got {len(window)}, need {expected_months}")
        return None
    
    return window


def index_to_100(series: pd.Series) -> pd.Series:
    """Re-index a series to start at 100."""
    first_value = series.iloc[0]
    if first_value == 0 or pd.isna(first_value):
        return series
    return series / first_value * 100


def calculate_forward_metrics(
    window: pd.DataFrame,
    lookback_months: int = 24
) -> dict:
    """
    Calculate forward period metrics.
    
    Returns dict with:
    - Forward returns for each asset (real, 12-month)
    - Volatilities for each asset
    - Benchmark 60/40 metrics
    """
    # Split into lookback and forward
    forward_start = lookback_months
    lookback_data = window.iloc[:forward_start]
    forward_data = window.iloc[forward_start:]
    
    if len(forward_data) < 11:  # Need at least 11 months for returns
        return None
    
    # Get values at split point and end
    split_idx = lookback_data.index[-1]
    end_idx = forward_data.index[-1]
    
    # Calculate 12-month forward returns (real)
    def calc_return(col):
        start_val = window.loc[split_idx, col]
        end_val = window.loc[end_idx, col]
        if start_val == 0 or pd.isna(start_val):
            return 0.0
        return (end_val / start_val) - 1
    
    returns = {
        'stocks': calc_return('idx_stocks_real'),
        'bonds': calc_return('idx_bonds_real'),
        'cash': calc_return('idx_cash_real'),
        'gold': calc_return('idx_gold_real'),
    }
    
    # Calculate monthly returns for volatility
    def calc_monthly_returns(col):
        return window[col].pct_change().iloc[forward_start:].dropna().tolist()
    
    monthly_returns = {
        'stocks': calc_monthly_returns('idx_stocks_real'),
        'bonds': calc_monthly_returns('idx_bonds_real'),
        'cash': calc_monthly_returns('idx_cash_real'),
        'gold': calc_monthly_returns('idx_gold_real'),
    }
    
    # Calculate annualized volatility
    def calc_volatility(monthly: list):
        if len(monthly) < 2:
            return 0.0
        std = np.std(monthly)
        return std * math.sqrt(12)  # Annualize
    
    volatilities = {
        'stocks': calc_volatility(monthly_returns['stocks']),
        'bonds': calc_volatility(monthly_returns['bonds']),
        'gold': calc_volatility(monthly_returns['gold']),
    }
    
    # Calculate benchmark (60/40) metrics
    benchmark_alloc = {'stocks': 60, 'bonds': 40, 'cash': 0, 'gold': 0}
    benchmark_return = sum(
        benchmark_alloc[a] / 100 * returns[a] for a in returns
    )
    
    # Benchmark monthly returns
    benchmark_monthly = []
    for i in range(len(monthly_returns['stocks'])):
        m_ret = sum(
            benchmark_alloc[a] / 100 * monthly_returns[a][i]
            for a in returns if i < len(monthly_returns[a])
        )
        benchmark_monthly.append(m_ret)
    
    benchmark_vol = calc_volatility(benchmark_monthly)
    risk_free = returns['cash']
    
    benchmark_sharpe = 0.0
    if benchmark_vol > 0:
        benchmark_sharpe = (benchmark_return - risk_free) / benchmark_vol
    
    return {
        'returns': returns,
        'volatilities': volatilities,
        'monthly_returns': monthly_returns,
        'benchmark_return': benchmark_return,
        'benchmark_sharpe': benchmark_sharpe,
    }


def create_scenario(
    db: Session,
    window: pd.DataFrame,
    start_date: pd.Timestamp,
    metrics: dict,
    label: str,
    context: str = None
) -> Scenario:
    """Create a scenario in the database."""
    # Convert numpy types to Python native types
    scenario = Scenario(
        actual_start_date=start_date.date(),
        display_label=label,
        historical_context=context,
        fwd_return_stocks=float(metrics['returns']['stocks']),
        fwd_return_bonds=float(metrics['returns']['bonds']),
        fwd_return_cash=float(metrics['returns']['cash']),
        fwd_return_gold=float(metrics['returns']['gold']),
        fwd_volatility_stocks=float(metrics['volatilities']['stocks']),
        fwd_volatility_bonds=float(metrics['volatilities']['bonds']),
        fwd_volatility_gold=float(metrics['volatilities']['gold']),
        benchmark_6040_return=float(metrics['benchmark_return']),
        benchmark_6040_sharpe=float(metrics['benchmark_sharpe']),
    )
    
    db.add(scenario)
    db.flush()  # Get the ID
    
    # Re-index all series to 100 at month 1
    stocks_indexed = index_to_100(window['idx_stocks_real'])
    bonds_indexed = index_to_100(window['idx_bonds_real'])
    cash_indexed = index_to_100(window['idx_cash_real'])
    gold_indexed = index_to_100(window['idx_gold_real'])
    
    # Create monthly data points
    for i, (idx, row) in enumerate(window.iterrows()):
        month_index = i + 1
        is_forward = month_index > 24
        
        data_point = ScenarioData(
            scenario_id=scenario.id,
            month_index=month_index,
            is_forward=is_forward,
            idx_stocks=float(stocks_indexed.iloc[i]),
            idx_bonds=float(bonds_indexed.iloc[i]),
            idx_cash=float(cash_indexed.iloc[i]),
            idx_gold=float(gold_indexed.iloc[i]),
            gdp_growth_yoy=float(row['gdp_growth_yoy']) if pd.notna(row['gdp_growth_yoy']) else None,
            unemployment_rate=float(row['unemployment_rate']) if pd.notna(row['unemployment_rate']) else None,
            inflation_rate_yoy=float(row['inflation_rate_yoy']) if pd.notna(row['inflation_rate_yoy']) else None,
            fed_funds_rate=float(row['fed_funds_rate']) if pd.notna(row['fed_funds_rate']) else None,
            industrial_prod_yoy=float(row['industrial_prod_yoy']) if pd.notna(row['industrial_prod_yoy']) else None,
        )
        db.add(data_point)
    
    return scenario


def generate_scenarios(
    start_dates: List[str] = None,
    clear_existing: bool = False
):
    """
    Generate all scenarios from start dates.
    
    Args:
        start_dates: List of ISO date strings (YYYY-MM-DD). Uses defaults if None.
        clear_existing: If True, delete all existing scenarios first.
    """
    if start_dates is None:
        start_dates = DEFAULT_START_DATES
    
    # Load data
    print("Loading normalized data...")
    df = load_normalized_data()
    print(f"  Loaded {len(df)} months of data")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        if clear_existing:
            print("Clearing existing scenarios...")
            db.query(ScenarioData).delete()
            db.query(Scenario).delete()
            db.commit()
        
        print(f"Generating {len(start_dates)} scenarios...")
        
        for i, date_str in enumerate(start_dates):
            label = f"Scenario {chr(65 + i)}"  # A, B, C, ...
            start_date = pd.Timestamp(date_str)
            context = HISTORICAL_CONTEXT.get(date_str, None)
            
            print(f"  [{i+1}/{len(start_dates)}] {date_str}: {context or label}")
            
            # Extract window
            window = extract_scenario_window(df, start_date)
            if window is None:
                print(f"    Skipping - insufficient data")
                continue
            
            # Calculate metrics
            metrics = calculate_forward_metrics(window)
            if metrics is None:
                print(f"    Skipping - could not calculate metrics")
                continue
            
            # Create scenario
            scenario = create_scenario(db, window, start_date, metrics, label, context)
            print(f"    Created scenario ID {scenario.id}")
            print(f"    Forward returns: Stocks={metrics['returns']['stocks']:.1%}, "
                  f"Bonds={metrics['returns']['bonds']:.1%}, "
                  f"Gold={metrics['returns']['gold']:.1%}")
        
        db.commit()
        print("\nScenarios generated successfully!")
        
        # Print summary
        count = db.query(Scenario).count()
        print(f"Total scenarios in database: {count}")
        
    finally:
        db.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate game scenarios")
    parser.add_argument(
        "--start-dates", 
        type=str, 
        help="JSON file with list of start dates"
    )
    parser.add_argument(
        "--clear", 
        action="store_true", 
        help="Clear existing scenarios"
    )
    
    args = parser.parse_args()
    
    start_dates = None
    if args.start_dates:
        with open(args.start_dates) as f:
            start_dates = json.load(f)
    
    print("=" * 60)
    print("Hindsight Economics - Scenario Generator")
    print("=" * 60)
    
    generate_scenarios(start_dates, clear_existing=args.clear)


if __name__ == "__main__":
    main()


