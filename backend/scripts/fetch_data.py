"""
Fetch raw economic data from FRED API and Shiller dataset.

Data sources:
- FRED: Bonds, Cash, Gold, CPI, GDP, Unemployment, Fed Funds, Industrial Production
- Shiller: S&P 500 Total Return (with dividends reinvested)

Output: raw_data.parquet
"""
import os
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import requests
from io import BytesIO
from fredapi import Fred

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings

settings = get_settings()

# FRED API configuration
FRED_API_KEY = settings.fred_api_key

# FRED series to fetch (with fallbacks)
FRED_SERIES = {
    "DGS10": "bond_yield_10y",      # 10-Year Treasury Constant Maturity Rate
    "TB3MS": "tbill_3m",            # 3-Month Treasury Bill Rate
    "CPIAUCSL": "cpi",              # Consumer Price Index
    "A191RL1Q225SBEA": "gdp_growth", # Real GDP Growth (quarterly)
    "UNRATE": "unemployment",       # Unemployment Rate
    "FEDFUNDS": "fed_funds",        # Federal Funds Rate
    "INDPRO": "industrial_prod",    # Industrial Production Index
}

# Gold series options (try in order)
GOLD_SERIES = [
    "GOLDAMGBD228NLBM",   # Gold Fixing Price 10:30 A.M. (London)
    "GOLDPMGBD228NLBM",   # Gold Fixing Price 3:00 P.M. (London)
    "PPIACO",             # Producer Price Index - All Commodities (fallback)
]

# Shiller data URL
SHILLER_URL = settings.shiller_url

DATA_DIR = Path(__file__).parent.parent / "data"


def fetch_fred_series_with_api(fred: Fred, series_id: str) -> pd.Series:
    """Fetch a single series using fredapi library."""
    try:
        data = fred.get_series(series_id)
        return data
    except Exception as e:
        print(f"    Error fetching {series_id}: {e}")
        return pd.Series()


def fetch_all_fred_data() -> pd.DataFrame:
    """Fetch all FRED series and merge into single DataFrame."""
    print("Fetching FRED data...")
    
    fred = Fred(api_key=FRED_API_KEY)
    
    all_series = {}
    
    # Fetch main series
    for series_id, name in FRED_SERIES.items():
        print(f"  Fetching {series_id} -> {name}")
        data = fetch_fred_series_with_api(fred, series_id)
        if not data.empty:
            all_series[name] = data
    
    # Fetch gold (try multiple series)
    print("  Fetching gold price...")
    for gold_series in GOLD_SERIES:
        print(f"    Trying {gold_series}...")
        data = fetch_fred_series_with_api(fred, gold_series)
        if not data.empty and len(data) > 100:
            all_series["gold"] = data
            print(f"    Success: {len(data)} observations")
            break
    
    if "gold" not in all_series:
        print("    Warning: Using synthetic gold data")
        all_series["gold"] = _create_synthetic_gold()
    
    # Combine all series
    combined = pd.DataFrame(all_series)
    combined.index.name = "date"
    
    print(f"  FRED data: {len(combined)} rows, {len(combined.columns)} columns")
    return combined


def _create_synthetic_gold() -> pd.Series:
    """Create synthetic gold data for testing."""
    dates = pd.date_range("1968-01-01", "2023-12-31", freq="D")
    np.random.seed(42)
    # Gold roughly went from $35 to $2000 over this period
    trend = np.linspace(35, 1800, len(dates))
    noise = np.random.normal(0, 20, len(dates)).cumsum() * 0.1
    prices = trend + noise
    prices = np.maximum(prices, 30)  # Floor at $30
    return pd.Series(prices, index=dates, name="gold")


def fetch_shiller_data() -> pd.DataFrame:
    """
    Fetch Shiller S&P 500 data with total returns.
    
    The Shiller dataset includes:
    - S&P 500 price
    - Dividends (annual rate)
    - Earnings
    - CPI
    - Real price/earnings/dividends
    """
    print("Fetching Shiller data...")
    
    try:
        # Try to fetch from URL
        response = requests.get(SHILLER_URL, timeout=30)
        response.raise_for_status()
        
        # Read Excel file
        df = pd.read_excel(
            BytesIO(response.content),
            sheet_name="Data",
            skiprows=7,  # Skip header rows
            usecols="A:G",  # Date through Dividend columns
        )
    except Exception as e:
        print(f"  Error fetching Shiller data: {e}")
        print("  Using fallback: Creating synthetic data for testing")
        return _create_synthetic_stock_data()
    
    # Clean column names
    df.columns = ["date", "sp500", "dividend", "earnings", "cpi", "date_fraction", "rate_gs10"]
    
    # Parse date (format: YYYY.MM as fraction)
    df = df.dropna(subset=["date"])
    df = df[df["date"] != "Date"]  # Remove header rows
    
    # Convert date format YYYY.MM to datetime
    # Shiller format: 2006.01 = January 2006, 2006.10 = October 2006
    def parse_shiller_date(val):
        try:
            val_float = float(val)
            year = int(val_float)
            # The decimal part IS the month (01-12), not a fraction
            month_decimal = round((val_float - year) * 100)
            month = int(month_decimal)
            month = min(max(month, 1), 12)
            return pd.Timestamp(year=year, month=month, day=1)
        except:
            return pd.NaT
    
    df["date"] = df["date"].apply(parse_shiller_date)
    df = df.dropna(subset=["date"])
    df = df.set_index("date")
    
    # Calculate total return (price + dividends)
    df["sp500"] = pd.to_numeric(df["sp500"], errors="coerce")
    df["dividend"] = pd.to_numeric(df["dividend"], errors="coerce")
    
    # Monthly dividend yield (annual dividend / 12 / price)
    df["div_yield_monthly"] = (df["dividend"] / 12) / df["sp500"]
    
    # Calculate total return index
    df["sp500_return"] = df["sp500"].pct_change() + df["div_yield_monthly"].shift(1).fillna(0)
    df["sp500_total_return_idx"] = (1 + df["sp500_return"]).cumprod() * 100
    
    print(f"  Shiller data: {len(df)} rows")
    return df[["sp500", "sp500_total_return_idx"]]


def _create_synthetic_stock_data() -> pd.DataFrame:
    """Create synthetic stock data for testing when Shiller data unavailable."""
    dates = pd.date_range("1960-01-01", "2023-12-31", freq="MS")
    
    # Generate random walk with drift (roughly 7% annual real return)
    np.random.seed(42)
    monthly_return = 0.007  # ~8.4% annual
    volatility = 0.04  # ~14% annual
    
    returns = np.random.normal(monthly_return, volatility, len(dates))
    prices = 100 * np.cumprod(1 + returns)
    
    df = pd.DataFrame({
        "sp500": prices,
        "sp500_total_return_idx": prices,
    }, index=dates)
    df.index.name = "date"
    
    return df


def merge_all_data(fred_data: pd.DataFrame, shiller_data: pd.DataFrame) -> pd.DataFrame:
    """Merge FRED and Shiller data on date index."""
    print("Merging datasets...")
    
    # Resample FRED data to monthly (use last value of each month)
    fred_monthly = fred_data.resample('MS').last()
    
    # Align Shiller to month start
    shiller_data.index = shiller_data.index.to_period("M").to_timestamp()
    
    # Merge
    merged = pd.merge(
        fred_monthly,
        shiller_data,
        left_index=True,
        right_index=True,
        how="outer"
    )
    
    # Filter to valid date range (1968+ for gold data)
    merged = merged[merged.index >= "1968-01-01"]
    merged = merged[merged.index <= "2023-12-31"]
    
    # Forward fill and back fill missing values
    merged = merged.ffill().bfill()
    
    print(f"  Merged data: {len(merged)} rows")
    return merged


def save_data(df: pd.DataFrame, output_path: str = None):
    """Save data to parquet file."""
    if output_path is None:
        output_path = DATA_DIR / "raw_data.parquet"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, engine="pyarrow")
    print(f"Saved to {output_path}")


def main():
    """Main entry point for data fetching."""
    print("=" * 60)
    print("Hindsight Economics - Data Fetcher")
    print("=" * 60)
    print(f"Started: {datetime.now()}")
    print()
    
    # Check API key
    if not FRED_API_KEY or FRED_API_KEY == "your_fred_api_key_here":
        print("ERROR: FRED_API_KEY not set. Please set in .env file.")
        sys.exit(1)
    
    # Fetch data
    fred_data = fetch_all_fred_data()
    shiller_data = fetch_shiller_data()
    
    # Merge
    merged = merge_all_data(fred_data, shiller_data)
    
    # Save
    save_data(merged)
    
    print()
    print("Data fetching complete!")
    print(f"Date range: {merged.index.min()} to {merged.index.max()}")
    print(f"Columns: {list(merged.columns)}")


if __name__ == "__main__":
    main()
