"""add_user_auth_tables

Revision ID: 45a13777a0e8
Revises: 001
Create Date: 2026-01-06 14:31:17.382600

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '45a13777a0e8'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('magic_link_token', sa.String(length=255), nullable=True),
        sa.Column('magic_link_expires', sa.DateTime(), nullable=True),
        sa.Column('session_token', sa.String(length=255), nullable=True),
        sa.Column('session_expires', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('games_played', sa.Integer(), nullable=True),
        sa.Column('avg_brier_score', sa.Integer(), nullable=True),
        sa.Column('avg_portfolio_return', sa.Integer(), nullable=True),
        sa.Column('wins_vs_benchmark', sa.Integer(), nullable=True),
        sa.Column('losses_vs_benchmark', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_session_token'), 'users', ['session_token'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Create magic link attempts table for rate limiting
    op.create_table('magic_link_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('attempted_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_magic_link_attempts_email'), 'magic_link_attempts', ['email'], unique=False)
    op.create_index(op.f('ix_magic_link_attempts_id'), 'magic_link_attempts', ['id'], unique=False)
    
    # Add user_id to game_sessions
    op.add_column('game_sessions', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_game_sessions_user_id'), 'game_sessions', ['user_id'], unique=False)
    op.create_foreign_key('fk_game_sessions_user_id', 'game_sessions', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    # Remove user_id from game_sessions
    op.drop_constraint('fk_game_sessions_user_id', 'game_sessions', type_='foreignkey')
    op.drop_index(op.f('ix_game_sessions_user_id'), table_name='game_sessions')
    op.drop_column('game_sessions', 'user_id')
    
    # Drop magic_link_attempts
    op.drop_index(op.f('ix_magic_link_attempts_id'), table_name='magic_link_attempts')
    op.drop_index(op.f('ix_magic_link_attempts_email'), table_name='magic_link_attempts')
    op.drop_table('magic_link_attempts')
    
    # Drop users
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_session_token'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
