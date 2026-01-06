"""Game session API endpoints."""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Scenario, ScenarioData, GameSession, User
from app.api.auth import get_current_user
from app.schemas import (
    GameCreateInput,
    GameSessionOut,
    GameRevealOut,
    PredictionResult,
    AllocationInput,
    ScenarioDataOut,
)
from app.schemas.game import MonthlyDataOut
from app.services.scoring import ScoringService

router = APIRouter()

# Historical descriptions for each scenario period
HISTORICAL_DESCRIPTIONS = {
    "Oil Crisis & Stagflation": (
        "The 1973 oil embargo sent shockwaves through the global economy. OPEC's production cuts "
        "quadrupled oil prices, triggering a severe recession combined with high inflation—a toxic "
        "combination known as 'stagflation.' The stock market lost nearly half its value, while gold "
        "and commodities soared as investors fled to inflation hedges."
    ),
    "Volcker Shock - Peak Interest Rates": (
        "Fed Chairman Paul Volcker launched an aggressive campaign to break the back of inflation, "
        "raising the federal funds rate to an unprecedented 20%. The resulting recession was severe "
        "but ultimately succeeded in taming double-digit inflation. This period marked the beginning "
        "of a historic bull market in bonds as rates began their multi-decade decline."
    ),
    "Early 80s Recession": (
        "The economy was emerging from the deepest recession since the Great Depression. Unemployment "
        "had peaked above 10%, but with inflation finally under control, the Fed began cutting rates. "
        "This set the stage for a powerful economic recovery and one of the greatest bull markets in history."
    ),
    "Pre-Black Monday": (
        "Markets had been on a tear, with the S&P 500 up over 40% in the preceding year. Valuations "
        "were stretched, and program trading was increasingly prevalent. The stage was set for the "
        "October 1987 crash, when the Dow Jones fell 22.6% in a single day—the largest one-day "
        "percentage decline in history."
    ),
    "Gulf War Recession": (
        "Iraq's invasion of Kuwait sent oil prices spiking and consumer confidence plummeting. "
        "The U.S. entered a brief but sharp recession, with the savings and loan crisis adding to "
        "financial sector stress. However, the swift military victory and falling oil prices set "
        "the stage for recovery."
    ),
    "Asian Financial Crisis & LTCM": (
        "Currency crises swept through Asian economies, causing global market turmoil. The collapse "
        "of Long-Term Capital Management—a massive hedge fund—nearly destabilized the entire financial "
        "system. The Fed orchestrated an emergency bailout and cut rates, eventually steadying markets. "
        "This period foreshadowed the risks of excessive leverage in financial markets."
    ),
    "Dot-com Peak": (
        "The technology bubble had reached its zenith. Companies with no profits commanded billion-dollar "
        "valuations based on 'eyeballs' and 'clicks.' The NASDAQ would soon lose 78% of its value as "
        "the bubble burst, marking one of the most spectacular market crashes in history. Traditional "
        "value investors who had been mocked for years were finally vindicated."
    ),
    "Post Dot-com Recovery": (
        "The economy was recovering from the tech bust and 9/11 attacks. The Fed had slashed rates "
        "to just 1%, sparking a housing boom and hunt for yield. While stocks began to recover, "
        "the seeds of the next crisis were being planted in the mortgage market."
    ),
    "Housing Boom Peak": (
        "The housing market was in full bubble territory. Subprime mortgages were being packaged into "
        "complex securities and sold worldwide. Home prices had doubled in many markets. Few recognized "
        "that this would become the worst financial crisis since the Great Depression, with home prices "
        "falling 30% nationally and the banking system nearly collapsing."
    ),
    "Pre-Financial Crisis": (
        "Warning signs were emerging. Subprime mortgage delinquencies were rising, and Bear Stearns "
        "hedge funds had already collapsed. Yet the stock market hit all-time highs, with many experts "
        "dismissing concerns as overblown. Within 18 months, the S&P 500 would lose more than half its value."
    ),
    "Global Financial Crisis": (
        "Lehman Brothers had just collapsed, triggering a global panic. Credit markets froze, and the "
        "financial system stood on the brink of total collapse. Massive government interventions—TARP, "
        "Fed emergency lending, and fiscal stimulus—would eventually stabilize the system. Stocks would "
        "bottom in March 2009, beginning one of the longest bull markets in history."
    ),
    "Post-GFC Recovery": (
        "The economy was slowly recovering from the worst recession in 80 years. The Fed's quantitative "
        "easing programs kept rates near zero and flooded markets with liquidity. European sovereign debt "
        "concerns created periodic scares, but markets continued their upward march."
    ),
    "European Debt Crisis": (
        "Greece's debt crisis threatened to unravel the eurozone. Fears of contagion to Italy and Spain "
        "sent bond yields soaring and stocks tumbling. ECB President Mario Draghi's pledge to do 'whatever "
        "it takes' to save the euro eventually calmed markets. U.S. markets proved resilient."
    ),
    "Post-Oil Crash": (
        "Oil prices had collapsed from over $100 to below $30 per barrel, devastating energy companies "
        "and emerging markets. China growth fears added to the turmoil, with the S&P 500 experiencing "
        "its worst start to a year ever. However, the U.S. consumer benefited from cheap gas, and "
        "markets recovered strongly."
    ),
    "Late Cycle Expansion": (
        "The economic expansion was getting long in the tooth. The Fed was gradually raising rates from "
        "post-crisis lows. Trade tensions with China were escalating, and the yield curve was flattening—"
        "historically a recession warning signal. Volatility returned in late 2018 with a sharp correction."
    ),
    "Pre-COVID Peak": (
        "Markets had just hit all-time highs, with unemployment at 50-year lows. Few anticipated that "
        "a novel coronavirus emerging in China would trigger a global pandemic, the fastest bear market "
        "in history (falling 34% in just 23 days), and unprecedented fiscal and monetary stimulus. "
        "The subsequent recovery would be equally dramatic."
    ),
}


@router.post("/", response_model=GameSessionOut)
def create_game(
    game_input: GameCreateInput, 
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a new game session with predictions, allocation, and rationale.
    Returns a session token for retrieving results.
    """
    # Get current user if authenticated
    current_user = get_current_user(request, db)
    
    # Verify scenario exists
    scenario = db.query(Scenario).filter(Scenario.id == game_input.scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Generate unique session token
    session_token = str(uuid.uuid4())
    
    # Create game session
    game_session = GameSession(
        scenario_id=game_input.scenario_id,
        session_token=session_token,
        user_id=current_user.id if current_user else None,
        pred_above_15pct=game_input.predictions.above_15pct,
        pred_above_10pct=game_input.predictions.above_10pct,
        pred_above_5pct=game_input.predictions.above_5pct,
        pred_above_0pct=game_input.predictions.above_0pct,
        alloc_stocks=game_input.allocation.stocks,
        alloc_bonds=game_input.allocation.bonds,
        alloc_cash=game_input.allocation.cash,
        alloc_gold=game_input.allocation.gold,
        rationale=game_input.rationale or "",
    )
    
    db.add(game_session)
    db.commit()
    db.refresh(game_session)
    
    return game_session


@router.get("/{session_token}/reveal", response_model=GameRevealOut)
def reveal_game(session_token: str, db: Session = Depends(get_db)):
    """
    Reveal the game results including actual outcomes, scores, and period details.
    This calculates and stores the scores if not already computed.
    """
    # Get game session
    game = (
        db.query(GameSession)
        .filter(GameSession.session_token == session_token)
        .first()
    )
    
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    # Get scenario
    scenario = db.query(Scenario).filter(Scenario.id == game.scenario_id).first()
    
    # Get all monthly data including forward period
    all_data = (
        db.query(ScenarioData)
        .filter(ScenarioData.scenario_id == scenario.id)
        .order_by(ScenarioData.month_index)
        .all()
    )
    
    # Extract forward period data for monthly returns calculation
    forward_data = [d for d in all_data if d.is_forward]
    
    # Calculate monthly returns for Sharpe calculation
    monthly_returns = _calculate_monthly_returns(all_data)
    
    # Prepare predictions dict
    predictions = {
        'above_15pct': float(game.pred_above_15pct),
        'above_10pct': float(game.pred_above_10pct),
        'above_5pct': float(game.pred_above_5pct),
        'above_0pct': float(game.pred_above_0pct),
    }
    
    # Prepare returns dict
    returns = {
        'stocks': float(scenario.fwd_return_stocks),
        'bonds': float(scenario.fwd_return_bonds),
        'cash': float(scenario.fwd_return_cash),
        'gold': float(scenario.fwd_return_gold),
    }
    
    # Prepare allocation dict
    allocation = {
        'stocks': game.alloc_stocks,
        'bonds': game.alloc_bonds,
        'cash': game.alloc_cash,
        'gold': game.alloc_gold,
    }
    
    # Calculate scores
    brier_score, prediction_results = ScoringService.calculate_brier_score(
        predictions, returns['stocks']
    )
    
    portfolio_return = ScoringService.calculate_portfolio_return(allocation, returns)
    
    risk_free_return = returns['cash']  # T-bill return as risk-free
    portfolio_sharpe = ScoringService.calculate_portfolio_sharpe(
        allocation, monthly_returns, risk_free_return
    )
    
    benchmark_metrics = ScoringService.calculate_benchmark_metrics(
        returns, monthly_returns, risk_free_return
    )
    
    excess_return = portfolio_return - benchmark_metrics['return']
    excess_sharpe = portfolio_sharpe - benchmark_metrics['sharpe']
    
    # Update game session with scores if not already done
    if game.completed_at is None:
        game.brier_score = brier_score
        game.portfolio_return = portfolio_return
        game.portfolio_sharpe = portfolio_sharpe
        game.vs_benchmark_return = excess_return
        game.vs_benchmark_sharpe = excess_sharpe
        game.completed_at = datetime.utcnow()
        db.commit()
    
    # Format period string
    # actual_start_date is month 24 (end of historical period)
    # Window starts 24 months before, ends 12 months after
    from dateutil.relativedelta import relativedelta
    scenario_start = scenario.actual_start_date
    window_start = scenario_start - relativedelta(months=23)  # Month 1
    window_end = scenario_start + relativedelta(months=12)  # Month 36
    actual_period = f"{window_start.strftime('%B %Y')} - {window_end.strftime('%B %Y')}"
    
    # Get historical description
    historical_description = HISTORICAL_DESCRIPTIONS.get(scenario.historical_context, None)
    
    # Convert monthly data for response
    monthly_data_out = [
        MonthlyDataOut(
            month_index=d.month_index,
            is_forward=d.is_forward,
            idx_stocks=float(d.idx_stocks),
            idx_bonds=float(d.idx_bonds),
            idx_cash=float(d.idx_cash),
            idx_gold=float(d.idx_gold),
            gdp_growth_yoy=float(d.gdp_growth_yoy) if d.gdp_growth_yoy else None,
            unemployment_rate=float(d.unemployment_rate) if d.unemployment_rate else None,
            inflation_rate_yoy=float(d.inflation_rate_yoy) if d.inflation_rate_yoy else None,
            fed_funds_rate=float(d.fed_funds_rate) if d.fed_funds_rate else None,
            industrial_prod_yoy=float(d.industrial_prod_yoy) if d.industrial_prod_yoy else None,
        )
        for d in all_data
    ]
    
    return GameRevealOut(
        session_token=session_token,
        actual_start_date=str(scenario.actual_start_date),
        actual_period=actual_period,
        historical_context=scenario.historical_context,
        historical_description=historical_description,
        monthly_data=monthly_data_out,
        prediction_results=[PredictionResult(**r) for r in prediction_results],
        brier_score=brier_score,
        allocation=AllocationInput(**allocation),
        asset_returns=returns,
        portfolio_return=portfolio_return,
        portfolio_sharpe=portfolio_sharpe,
        benchmark_return=benchmark_metrics['return'],
        benchmark_sharpe=benchmark_metrics['sharpe'],
        excess_return=excess_return,
        excess_sharpe=excess_sharpe,
        rationale=game.rationale,
    )


class UsernameInput(BaseModel):
    username: str


@router.post("/{session_token}/leaderboard")
def join_leaderboard(session_token: str, data: UsernameInput, db: Session = Depends(get_db)):
    """Opt into the leaderboard with a username."""
    game = (
        db.query(GameSession)
        .filter(GameSession.session_token == session_token)
        .first()
    )
    
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    if game.completed_at is None:
        raise HTTPException(status_code=400, detail="Game must be completed first")
    
    # Validate username
    if len(data.username) < 3 or len(data.username) > 50:
        raise HTTPException(status_code=400, detail="Username must be 3-50 characters")
    
    game.username = data.username
    db.commit()
    
    return {"message": "Successfully joined leaderboard", "username": data.username}


class ReflectionInput(BaseModel):
    reflection: str


@router.post("/{session_token}/reflection")
def add_reflection(session_token: str, data: ReflectionInput, db: Session = Depends(get_db)):
    """Add a reflection after seeing results."""
    game = (
        db.query(GameSession)
        .filter(GameSession.session_token == session_token)
        .first()
    )
    
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    game.reflection = data.reflection
    db.commit()
    
    return {"message": "Reflection saved"}


def _calculate_monthly_returns(all_data: list) -> dict:
    """Calculate monthly returns from indexed price data."""
    monthly_returns = {
        'stocks': [],
        'bonds': [],
        'cash': [],
        'gold': [],
    }
    
    # We need months 24-36 for forward period monthly returns (12 months)
    forward_months = [d for d in all_data if d.month_index > 24]
    
    # Get month 24 as the base for first forward return
    month_24 = next((d for d in all_data if d.month_index == 24), None)
    
    if month_24 and forward_months:
        prev_stocks = float(month_24.idx_stocks)
        prev_bonds = float(month_24.idx_bonds)
        prev_cash = float(month_24.idx_cash)
        prev_gold = float(month_24.idx_gold)
        
        for month in sorted(forward_months, key=lambda x: x.month_index):
            monthly_returns['stocks'].append(
                (float(month.idx_stocks) - prev_stocks) / prev_stocks
            )
            monthly_returns['bonds'].append(
                (float(month.idx_bonds) - prev_bonds) / prev_bonds
            )
            monthly_returns['cash'].append(
                (float(month.idx_cash) - prev_cash) / prev_cash
            )
            monthly_returns['gold'].append(
                (float(month.idx_gold) - prev_gold) / prev_gold
            )
            
            prev_stocks = float(month.idx_stocks)
            prev_bonds = float(month.idx_bonds)
            prev_cash = float(month.idx_cash)
            prev_gold = float(month.idx_gold)
    
    return monthly_returns
