"""Scoring service for Brier scores and portfolio metrics."""
from typing import Dict, List, Tuple
import math


class ScoringService:
    """Calculate game scores including Brier score and portfolio metrics."""
    
    @staticmethod
    def calculate_brier_score(
        predictions: Dict[str, float],
        actual_return: float
    ) -> Tuple[float, List[Dict]]:
        """
        Calculate Brier score for market predictions.
        
        Args:
            predictions: Dict with keys 'above_15pct', 'above_10pct', 'above_5pct', 'above_0pct'
                        Values are probabilities (0.0 to 1.0) that returns exceed threshold
            actual_return: The actual 12-month real return (e.g., 0.15 for 15%)
        
        Returns:
            Tuple of (brier_score, prediction_results)
            - brier_score: Average squared error (lower is better)
            - prediction_results: List of dicts with details for each prediction
        """
        thresholds = [
            ('above_15pct', 0.15, '>15%'),
            ('above_10pct', 0.10, '>10%'),
            ('above_5pct', 0.05, '>5%'),
            ('above_0pct', 0.00, '>0%'),
        ]
        
        results = []
        total_brier = 0.0
        
        for key, threshold, display in thresholds:
            prob_yes = predictions[key]
            actual_outcome = actual_return > threshold
            outcome_value = 1.0 if actual_outcome else 0.0
            
            # Brier score contribution: (probability - outcome)^2
            brier_contribution = (prob_yes - outcome_value) ** 2
            total_brier += brier_contribution
            
            # Determine user's prediction and confidence
            if prob_yes >= 0.5:
                user_prediction = "Yes"
                user_confidence = prob_yes
            else:
                user_prediction = "No"
                user_confidence = 1.0 - prob_yes
            
            correct = (user_prediction == "Yes") == actual_outcome
            
            results.append({
                'threshold': display,
                'user_prediction': user_prediction,
                'user_confidence': round(user_confidence, 3),
                'actual_outcome': actual_outcome,
                'correct': correct,
                'brier_contribution': round(brier_contribution, 4),
            })
        
        brier_score = total_brier / len(thresholds)
        return round(brier_score, 4), results
    
    @staticmethod
    def calculate_portfolio_return(
        allocation: Dict[str, int],
        returns: Dict[str, float]
    ) -> float:
        """
        Calculate weighted portfolio return.
        
        Args:
            allocation: Dict with keys 'stocks', 'bonds', 'cash', 'gold' (values 0-100, sum to 100)
            returns: Dict with keys 'stocks', 'bonds', 'cash', 'gold' (real returns as decimals)
        
        Returns:
            Portfolio return as decimal (e.g., 0.08 for 8%)
        """
        portfolio_return = 0.0
        for asset in ['stocks', 'bonds', 'cash', 'gold']:
            weight = allocation[asset] / 100.0
            portfolio_return += weight * returns[asset]
        
        return round(portfolio_return, 4)
    
    @staticmethod
    def calculate_portfolio_sharpe(
        allocation: Dict[str, int],
        monthly_returns: Dict[str, List[float]],
        risk_free_return: float
    ) -> float:
        """
        Calculate portfolio Sharpe ratio.
        
        Args:
            allocation: Dict with asset weights (0-100, sum to 100)
            monthly_returns: Dict mapping asset to list of 12 monthly returns
            risk_free_return: Annualized risk-free return (from T-bills)
        
        Returns:
            Sharpe ratio
        """
        # Calculate monthly portfolio returns
        portfolio_monthly = []
        for i in range(12):
            monthly_return = 0.0
            for asset in ['stocks', 'bonds', 'cash', 'gold']:
                weight = allocation[asset] / 100.0
                monthly_return += weight * monthly_returns[asset][i]
            portfolio_monthly.append(monthly_return)
        
        # Calculate annualized return
        cumulative = 1.0
        for r in portfolio_monthly:
            cumulative *= (1 + r)
        annualized_return = cumulative - 1
        
        # Calculate annualized volatility
        mean_monthly = sum(portfolio_monthly) / len(portfolio_monthly)
        variance = sum((r - mean_monthly) ** 2 for r in portfolio_monthly) / len(portfolio_monthly)
        monthly_std = math.sqrt(variance)
        annualized_std = monthly_std * math.sqrt(12)
        
        # Sharpe ratio
        if annualized_std == 0:
            return 0.0
        
        sharpe = (annualized_return - risk_free_return) / annualized_std
        return round(sharpe, 4)
    
    @staticmethod
    def calculate_benchmark_metrics(
        returns: Dict[str, float],
        monthly_returns: Dict[str, List[float]],
        risk_free_return: float,
        benchmark_allocation: Dict[str, int] = None
    ) -> Dict[str, float]:
        """
        Calculate benchmark (60/40) portfolio metrics.
        
        Args:
            returns: Annual returns per asset
            monthly_returns: Monthly returns per asset
            risk_free_return: Annualized risk-free return
            benchmark_allocation: Custom benchmark (default 60/40)
        
        Returns:
            Dict with 'return' and 'sharpe' for benchmark
        """
        if benchmark_allocation is None:
            benchmark_allocation = {'stocks': 60, 'bonds': 40, 'cash': 0, 'gold': 0}
        
        benchmark_return = ScoringService.calculate_portfolio_return(
            benchmark_allocation, returns
        )
        benchmark_sharpe = ScoringService.calculate_portfolio_sharpe(
            benchmark_allocation, monthly_returns, risk_free_return
        )
        
        return {
            'return': benchmark_return,
            'sharpe': benchmark_sharpe,
        }
    
    @staticmethod
    def get_brier_interpretation(score: float) -> str:
        """Return interpretation of Brier score."""
        if score < 0.10:
            return "Excellent calibration"
        elif score < 0.15:
            return "Good calibration"
        elif score < 0.20:
            return "Decent calibration"
        elif score < 0.25:
            return "Poor calibration (near random)"
        else:
            return "Worse than random guessing"
    
    @staticmethod
    def calculate_optimal_allocation(returns: Dict[str, float]) -> Dict[str, int]:
        """
        Calculate the optimal allocation based on actual returns.
        With hindsight, the optimal allocation is 100% in the best-performing asset.
        
        Args:
            returns: Dict with keys 'stocks', 'bonds', 'cash', 'gold' (real returns as decimals)
        
        Returns:
            Dict with optimal allocation (100% in best asset, 0% elsewhere)
        """
        # Find the best performing asset
        best_asset = max(returns, key=returns.get)
        
        return {
            'stocks': 100 if best_asset == 'stocks' else 0,
            'bonds': 100 if best_asset == 'bonds' else 0,
            'cash': 100 if best_asset == 'cash' else 0,
            'gold': 100 if best_asset == 'gold' else 0,
        }
    
    @staticmethod
    def calculate_optimal_metrics(
        returns: Dict[str, float],
        monthly_returns: Dict[str, List[float]],
        risk_free_return: float
    ) -> Dict[str, float]:
        """
        Calculate metrics for the optimal allocation.
        
        Args:
            returns: Annual returns per asset
            monthly_returns: Monthly returns per asset
            risk_free_return: Annualized risk-free return
        
        Returns:
            Dict with 'return', 'sharpe', and 'allocation' for optimal portfolio
        """
        optimal_allocation = ScoringService.calculate_optimal_allocation(returns)
        
        optimal_return = ScoringService.calculate_portfolio_return(
            optimal_allocation, returns
        )
        optimal_sharpe = ScoringService.calculate_portfolio_sharpe(
            optimal_allocation, monthly_returns, risk_free_return
        )
        
        return {
            'return': optimal_return,
            'sharpe': optimal_sharpe,
            'allocation': optimal_allocation,
        }


