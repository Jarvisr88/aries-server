"""Add claim status history table

Revision ID: 2024_12_19_01
Revises: 411900182b81
Create Date: 2024-12-19 16:24:17.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2024_12_19_01'
down_revision: Union[str, None] = '411900182b81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create claim_status_history table
    op.create_table('claim_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),  # Using String instead of Enum to avoid conflicts
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=50), nullable=True),
        sa.Column('updated_by', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for better query performance
    op.create_index(
        'ix_claim_status_history_claim_id',
        'claim_status_history',
        ['claim_id']
    )
    op.create_index(
        'ix_claim_status_history_status',
        'claim_status_history',
        ['status']
    )

def downgrade() -> None:
    op.drop_index('ix_claim_status_history_status')
    op.drop_index('ix_claim_status_history_claim_id')
    op.drop_table('claim_status_history')
