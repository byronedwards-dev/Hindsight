"""Scenario API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models import Scenario, ScenarioData
from app.schemas import ScenarioBase, ScenarioHistoryOut, ScenarioDataOut

router = APIRouter()


@router.get("/random", response_model=ScenarioBase)
def get_random_scenario(db: Session = Depends(get_db)):
    """Get a random scenario ID for a new game."""
    scenario = db.query(Scenario).order_by(func.random()).first()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="No scenarios available")
    
    return scenario


@router.get("/{scenario_id}/history", response_model=ScenarioHistoryOut)
def get_scenario_history(scenario_id: int, db: Session = Depends(get_db)):
    """
    Get the 24-month historical data for a scenario.
    Dates are obscured (Month 1, Month 2, etc).
    """
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Only return historical data (months 1-24, is_forward=False)
    historical_data = (
        db.query(ScenarioData)
        .filter(
            ScenarioData.scenario_id == scenario_id,
            ScenarioData.is_forward == False
        )
        .order_by(ScenarioData.month_index)
        .all()
    )
    
    return ScenarioHistoryOut(
        scenario_id=scenario.id,
        display_label=scenario.display_label,
        monthly_data=[ScenarioDataOut.model_validate(d) for d in historical_data]
    )


@router.get("/", response_model=List[ScenarioBase])
def list_scenarios(db: Session = Depends(get_db)):
    """List all available scenarios (for debugging/admin)."""
    scenarios = db.query(Scenario).all()
    return scenarios


