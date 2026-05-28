"""schema snapshot — initial migration stamping all existing tables.

Revision ID: 0d2fdb18cbdf
Revises: None (first migration)
Create Date: 2026-05-28 00:13:26.752407

NOTE: All tables already exist in the DB (created via init_db.py).
      This migration only records the current state so future changes
      can be tracked with 'flask db migrate' + 'flask db upgrade'.
      The upgrade() is intentionally empty — tables are already there.
      The downgrade() is a no-op for safety.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision      = '0d2fdb18cbdf'
down_revision = None          # first migration — no parent
branch_labels = None
depends_on    = None


def upgrade():
    # Tables already exist — nothing to create.
    # Alembic will stamp this revision as 'current' when run.
    pass


def downgrade():
    # Safety: do not drop tables on downgrade.
    pass
