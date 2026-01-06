"""Leaderboard API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import GameSession
from app.schemas import LeaderboardOut, LeaderboardEntry

router = APIRouter()


@router.get("/", response_model=LeaderboardOut)
def get_leaderboard(
    limit: int = Query(default=50, ge=1, le=100),
    username: str = Query(default=None, description="Get rank for specific user"),
    db: Session = Depends(get_db)
):
    """
    Get the leaderboard with top players.
    Optionally include the requesting user's rank.
    """
    # Aggregate stats by username
    leaderboard_query = (
        db.query(
            GameSession.username,
            func.count(GameSession.id).label('games_played'),
            func.avg(GameSession.brier_score).label('avg_brier_score'),
            func.avg(GameSession.portfolio_sharpe).label('avg_sharpe'),
            func.avg(GameSession.vs_benchmark_return).label('avg_excess_return'),
        )
        .filter(
            GameSession.username.isnot(None),
            GameSession.completed_at.isnot(None),
        )
        .group_by(GameSession.username)
        .order_by(
            func.avg(GameSession.brier_score).asc(),  # Lower Brier is better
            func.avg(GameSession.portfolio_sharpe).desc(),
        )
    )
    
    all_entries = leaderboard_query.all()
    
    # Build leaderboard entries
    entries = []
    user_rank = None
    user_stats = None
    
    for idx, row in enumerate(all_entries):
        rank = idx + 1
        entry = LeaderboardEntry(
            rank=rank,
            username=row.username,
            games_played=row.games_played,
            avg_brier_score=round(float(row.avg_brier_score or 0), 4),
            avg_sharpe=round(float(row.avg_sharpe or 0), 4),
            avg_excess_return=round(float(row.avg_excess_return or 0), 4),
        )
        
        if rank <= limit:
            entries.append(entry)
        
        if username and row.username == username:
            user_rank = rank
            user_stats = entry
    
    return LeaderboardOut(
        entries=entries,
        user_rank=user_rank,
        user_stats=user_stats,
    )


@router.get("/stats/{username}")
def get_user_stats(username: str, db: Session = Depends(get_db)):
    """Get detailed stats for a specific user."""
    games = (
        db.query(GameSession)
        .filter(
            GameSession.username == username,
            GameSession.completed_at.isnot(None),
        )
        .all()
    )
    
    if not games:
        return {"message": "No games found for this user"}
    
    # Calculate stats
    total_games = len(games)
    avg_brier = sum(float(g.brier_score or 0) for g in games) / total_games
    avg_sharpe = sum(float(g.portfolio_sharpe or 0) for g in games) / total_games
    avg_excess = sum(float(g.vs_benchmark_return or 0) for g in games) / total_games
    
    best_brier_game = min(games, key=lambda g: float(g.brier_score or 999))
    best_sharpe_game = max(games, key=lambda g: float(g.portfolio_sharpe or -999))
    
    return {
        "username": username,
        "games_played": total_games,
        "avg_brier_score": round(avg_brier, 4),
        "avg_sharpe": round(avg_sharpe, 4),
        "avg_excess_return": round(avg_excess, 4),
        "best_brier_score": round(float(best_brier_game.brier_score or 0), 4),
        "best_sharpe": round(float(best_sharpe_game.portfolio_sharpe or 0), 4),
    }


