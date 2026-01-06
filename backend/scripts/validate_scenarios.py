"""
Validate generated scenarios for data quality.

Checks:
1. All scenarios have 36 months of data
2. No missing values in critical fields
3. Index values are reasonable (no extreme outliers)
4. Forward returns are within expected bounds
5. Macro indicators are reasonable
"""
import sys
from pathlib import Path

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Scenario, ScenarioData


def validate_scenarios():
    """Run all validation checks on scenarios."""
    db = SessionLocal()
    
    try:
        scenarios = db.query(Scenario).all()
        
        if not scenarios:
            print("No scenarios found in database!")
            return False
        
        print(f"Validating {len(scenarios)} scenarios...")
        print()
        
        all_valid = True
        
        for scenario in scenarios:
            print(f"Scenario {scenario.id}: {scenario.display_label}")
            print(f"  Date: {scenario.actual_start_date}")
            print(f"  Context: {scenario.historical_context}")
            
            issues = []
            
            # Check monthly data count
            data_count = (
                db.query(ScenarioData)
                .filter(ScenarioData.scenario_id == scenario.id)
                .count()
            )
            if data_count != 36:
                issues.append(f"Expected 36 months, got {data_count}")
            
            # Check forward returns are reasonable (-50% to +100%)
            returns = {
                'stocks': float(scenario.fwd_return_stocks or 0),
                'bonds': float(scenario.fwd_return_bonds or 0),
                'cash': float(scenario.fwd_return_cash or 0),
                'gold': float(scenario.fwd_return_gold or 0),
            }
            
            for asset, ret in returns.items():
                if ret < -0.5 or ret > 1.0:
                    issues.append(f"Unusual {asset} return: {ret:.1%}")
            
            # Check volatilities are positive
            vols = {
                'stocks': float(scenario.fwd_volatility_stocks or 0),
                'bonds': float(scenario.fwd_volatility_bonds or 0),
                'gold': float(scenario.fwd_volatility_gold or 0),
            }
            
            for asset, vol in vols.items():
                if vol < 0 or vol > 1.0:
                    issues.append(f"Unusual {asset} volatility: {vol:.1%}")
            
            # Check indexed values
            monthly_data = (
                db.query(ScenarioData)
                .filter(ScenarioData.scenario_id == scenario.id)
                .order_by(ScenarioData.month_index)
                .all()
            )
            
            # First month should be indexed to 100
            if monthly_data:
                first = monthly_data[0]
                if abs(float(first.idx_stocks) - 100) > 0.1:
                    issues.append(f"First month stocks not indexed to 100: {first.idx_stocks}")
            
            # Check for NaN values in indices
            for m in monthly_data:
                for attr in ['idx_stocks', 'idx_bonds', 'idx_cash', 'idx_gold']:
                    val = getattr(m, attr)
                    if val is None or np.isnan(float(val)):
                        issues.append(f"NaN in {attr} at month {m.month_index}")
                        break
            
            # Check macro indicators are in reasonable ranges
            for m in monthly_data:
                if m.unemployment_rate is not None:
                    u = float(m.unemployment_rate)
                    if u < 2 or u > 15:
                        issues.append(f"Unusual unemployment at month {m.month_index}: {u}%")
                        break
                
                if m.inflation_rate_yoy is not None:
                    inf = float(m.inflation_rate_yoy)
                    if inf < -5 or inf > 20:
                        issues.append(f"Unusual inflation at month {m.month_index}: {inf}%")
                        break
            
            # Print results
            if issues:
                all_valid = False
                print(f"  ❌ ISSUES:")
                for issue in issues:
                    print(f"     - {issue}")
            else:
                print(f"  ✓ Valid")
                print(f"  Returns: Stocks={returns['stocks']:.1%}, "
                      f"Bonds={returns['bonds']:.1%}, Gold={returns['gold']:.1%}")
            
            print()
        
        # Summary
        print("=" * 60)
        if all_valid:
            print("✓ All scenarios passed validation!")
        else:
            print("❌ Some scenarios have issues. Please review.")
        
        return all_valid
        
    finally:
        db.close()


def print_scenario_summary():
    """Print a summary table of all scenarios."""
    db = SessionLocal()
    
    try:
        scenarios = db.query(Scenario).order_by(Scenario.actual_start_date).all()
        
        if not scenarios:
            print("No scenarios found.")
            return
        
        print("\n" + "=" * 80)
        print("SCENARIO SUMMARY")
        print("=" * 80)
        print(f"{'ID':<4} {'Date':<12} {'Context':<30} {'Stocks':<10} {'Bonds':<10} {'Gold':<10}")
        print("-" * 80)
        
        for s in scenarios:
            print(
                f"{s.id:<4} "
                f"{str(s.actual_start_date):<12} "
                f"{(s.historical_context or '')[:28]:<30} "
                f"{float(s.fwd_return_stocks or 0):>+8.1%} "
                f"{float(s.fwd_return_bonds or 0):>+8.1%} "
                f"{float(s.fwd_return_gold or 0):>+8.1%}"
            )
        
        print("-" * 80)
        print(f"Total: {len(scenarios)} scenarios")
        
    finally:
        db.close()


def main():
    print("=" * 60)
    print("Hindsight Economics - Scenario Validator")
    print("=" * 60)
    print()
    
    valid = validate_scenarios()
    print_scenario_summary()
    
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())


