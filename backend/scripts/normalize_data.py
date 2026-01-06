"""
Normalize raw data for scenario generation.

This script:
1. Loads raw_data.parquet
2. Converts bond yields to price returns
3. Calculates real (inflation-adjusted) returns
4. Computes year-over-year macro indicators
5. Saves normalized data

Output: normalized_data.parquet
"""
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

DATA_DIR = Path(__file__).parent.parent / "data"


def load_raw_data() -> pd.DataFrame:
    """Load raw data from parquet file."""
    path = DATA_DIR / "raw_data.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Raw data not found at {path}. Run fetch_data.py first.")
    
    return pd.read_parquet(path)


def calculate_bond_returns(df: pd.DataFrame) -> pd.Series:
    """
    Convert bond yields to approximate price returns.
    
    Uses duration approximation:
    Price Return ≈ -Duration × ΔYield + Yield/12
    
    Assumes ~7 year duration for 10-year Treasury
    """
    duration = 7.0
    yields = df["bond_yield_10y"] / 100  # Convert to decimal
    
    # Monthly yield change
    yield_change = yields.diff()
    
    # Approximate monthly return: coupon income - price change
    monthly_return = yields / 12 - duration * yield_change
    
    # Build total return index
    return_idx = (1 + monthly_return).cumprod() * 100
    return_idx = return_idx.fillna(100)
    
    return return_idx


def calculate_cash_returns(df: pd.DataFrame) -> pd.Series:
    """
    Calculate T-bill total return index.
    
    T-bill rate is already an annualized yield, so monthly return = rate/12
    """
    monthly_rate = df["tbill_3m"] / 100 / 12
    return_idx = (1 + monthly_rate).cumprod() * 100
    return_idx = return_idx.fillna(100)
    
    return return_idx


def calculate_gold_returns(df: pd.DataFrame) -> pd.Series:
    """Calculate gold total return index from price levels."""
    # Gold is just price (no yield), so use price as index
    gold_normalized = df["gold"] / df["gold"].iloc[0] * 100
    return gold_normalized


def calculate_real_returns(
    nominal_returns: pd.Series, 
    cpi: pd.Series
) -> pd.Series:
    """
    Convert nominal returns to real (inflation-adjusted) returns.
    
    Real Return Index = Nominal Return Index / CPI Index × 100
    """
    cpi_normalized = cpi / cpi.iloc[0]
    real_returns = nominal_returns / cpi_normalized
    return real_returns


def calculate_yoy_changes(series: pd.Series) -> pd.Series:
    """Calculate year-over-year percentage change."""
    return series.pct_change(12) * 100


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main normalization pipeline.
    
    Returns DataFrame with:
    - Real total return indices for stocks, bonds, cash, gold
    - YoY macro indicators
    """
    print("Normalizing data...")
    
    # Remove duplicate indices if any
    if df.index.duplicated().any():
        print("  Removing duplicate dates...")
        df = df[~df.index.duplicated(keep='last')]
    
    result = pd.DataFrame(index=df.index)
    
    # Calculate nominal return indices
    print("  Calculating return indices...")
    result["idx_stocks_nominal"] = df["sp500_total_return_idx"]
    result["idx_bonds_nominal"] = calculate_bond_returns(df)
    result["idx_cash_nominal"] = calculate_cash_returns(df)
    result["idx_gold_nominal"] = calculate_gold_returns(df)
    
    # Normalize to first value = 100
    for col in ["idx_stocks_nominal", "idx_bonds_nominal", "idx_cash_nominal", "idx_gold_nominal"]:
        first_valid = result[col].first_valid_index()
        if first_valid is not None:
            first_val = result.loc[first_valid, col]
            if first_val != 0 and not pd.isna(first_val):
                result[col] = (result[col] / first_val * 100).values
    
    # Calculate real return indices
    print("  Calculating real returns...")
    cpi = df["cpi"]
    result["idx_stocks_real"] = calculate_real_returns(result["idx_stocks_nominal"], cpi)
    result["idx_bonds_real"] = calculate_real_returns(result["idx_bonds_nominal"], cpi)
    result["idx_cash_real"] = calculate_real_returns(result["idx_cash_nominal"], cpi)
    result["idx_gold_real"] = calculate_real_returns(result["idx_gold_nominal"], cpi)
    
    # Calculate YoY macro indicators
    print("  Calculating macro indicators...")
    
    # GDP growth is already YoY from FRED (quarterly, we'll forward fill)
    result["gdp_growth_yoy"] = df["gdp_growth"].ffill()
    
    # Unemployment rate (level, not change)
    result["unemployment_rate"] = df["unemployment"]
    
    # Inflation rate (YoY CPI change)
    result["inflation_rate_yoy"] = calculate_yoy_changes(cpi)
    
    # Fed funds rate (level)
    result["fed_funds_rate"] = df["fed_funds"]
    
    # Industrial production (YoY change)
    result["industrial_prod_yoy"] = calculate_yoy_changes(df["industrial_prod"])
    
    # Keep raw values for reference
    result["cpi"] = cpi
    result["tbill_3m"] = df["tbill_3m"]
    
    # Drop rows with too many NaN values
    result = result.dropna(thresh=len(result.columns) - 3)
    
    print(f"  Normalized data: {len(result)} rows")
    return result


def save_normalized_data(df: pd.DataFrame):
    """Save normalized data to parquet."""
    output_path = DATA_DIR / "normalized_data.parquet"
    df.to_parquet(output_path, engine="pyarrow")
    print(f"Saved to {output_path}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Hindsight Economics - Data Normalizer")
    print("=" * 60)
    
    # Load raw data
    raw = load_raw_data()
    print(f"Loaded raw data: {len(raw)} rows")
    
    # Normalize
    normalized = normalize_data(raw)
    
    # Save
    save_normalized_data(normalized)
    
    print()
    print("Normalization complete!")
    print(f"Date range: {normalized.index.min()} to {normalized.index.max()}")


if __name__ == "__main__":
    main()


