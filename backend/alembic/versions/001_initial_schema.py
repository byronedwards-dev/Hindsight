"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create scenarios table
    op.create_table(
        'scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actual_start_date', sa.Date(), nullable=False),
        sa.Column('display_label', sa.String(50), nullable=True),
        sa.Column('historical_context', sa.String(200), nullable=True),
        sa.Column('fwd_return_stocks', sa.Numeric(8, 4), nullable=True),
        sa.Column('fwd_return_bonds', sa.Numeric(8, 4), nullable=True),
        sa.Column('fwd_return_cash', sa.Numeric(8, 4), nullable=True),
        sa.Column('fwd_return_gold', sa.Numeric(8, 4), nullable=True),
        sa.Column('fwd_volatility_stocks', sa.Numeric(8, 4), nullable=True),
        sa.Column('fwd_volatility_bonds', sa.Numeric(8, 4), nullable=True),
        sa.Column('fwd_volatility_gold', sa.Numeric(8, 4), nullable=True),
        sa.Column('benchmark_6040_return', sa.Numeric(8, 4), nullable=True),
        sa.Column('benchmark_6040_sharpe', sa.Numeric(8, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scenarios_id'), 'scenarios', ['id'], unique=False)

    # Create scenario_data table
    op.create_table(
        'scenario_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('month_index', sa.Integer(), nullable=False),
        sa.Column('is_forward', sa.Boolean(), default=False),
        sa.Column('idx_stocks', sa.Numeric(10, 4), nullable=True),
        sa.Column('idx_bonds', sa.Numeric(10, 4), nullable=True),
        sa.Column('idx_cash', sa.Numeric(10, 4), nullable=True),
        sa.Column('idx_gold', sa.Numeric(10, 4), nullable=True),
        sa.Column('gdp_growth_yoy', sa.Numeric(6, 2), nullable=True),
        sa.Column('unemployment_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('inflation_rate_yoy', sa.Numeric(6, 2), nullable=True),
        sa.Column('fed_funds_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('industrial_prod_yoy', sa.Numeric(6, 2), nullable=True),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scenario_id', 'month_index', name='unique_scenario_month')
    )
    op.create_index(op.f('ix_scenario_data_id'), 'scenario_data', ['id'], unique=False)

    # Create game_sessions table
    op.create_table(
        'game_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(64), nullable=False),
        sa.Column('username', sa.String(50), nullable=True),
        sa.Column('pred_above_15pct', sa.Numeric(4, 3), nullable=True),
        sa.Column('pred_above_10pct', sa.Numeric(4, 3), nullable=True),
        sa.Column('pred_above_5pct', sa.Numeric(4, 3), nullable=True),
        sa.Column('pred_above_0pct', sa.Numeric(4, 3), nullable=True),
        sa.Column('alloc_stocks', sa.Integer(), nullable=True),
        sa.Column('alloc_bonds', sa.Integer(), nullable=True),
        sa.Column('alloc_cash', sa.Integer(), nullable=True),
        sa.Column('alloc_gold', sa.Integer(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('brier_score', sa.Numeric(6, 4), nullable=True),
        sa.Column('portfolio_return', sa.Numeric(8, 4), nullable=True),
        sa.Column('portfolio_sharpe', sa.Numeric(6, 4), nullable=True),
        sa.Column('vs_benchmark_return', sa.Numeric(8, 4), nullable=True),
        sa.Column('vs_benchmark_sharpe', sa.Numeric(6, 4), nullable=True),
        sa.Column('reflection', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('alloc_stocks >= 0 AND alloc_stocks <= 100', name='check_alloc_stocks'),
        sa.CheckConstraint('alloc_bonds >= 0 AND alloc_bonds <= 100', name='check_alloc_bonds'),
        sa.CheckConstraint('alloc_cash >= 0 AND alloc_cash <= 100', name='check_alloc_cash'),
        sa.CheckConstraint('alloc_gold >= 0 AND alloc_gold <= 100', name='check_alloc_gold'),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_sessions_id'), 'game_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_game_sessions_session_token'), 'game_sessions', ['session_token'], unique=True)
    op.create_index(op.f('ix_game_sessions_username'), 'game_sessions', ['username'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_game_sessions_username'), table_name='game_sessions')
    op.drop_index(op.f('ix_game_sessions_session_token'), table_name='game_sessions')
    op.drop_index(op.f('ix_game_sessions_id'), table_name='game_sessions')
    op.drop_table('game_sessions')
    
    op.drop_index(op.f('ix_scenario_data_id'), table_name='scenario_data')
    op.drop_table('scenario_data')
    
    op.drop_index(op.f('ix_scenarios_id'), table_name='scenarios')
    op.drop_table('scenarios')


