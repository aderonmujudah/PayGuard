"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-15

Creates the full MVP schema from the SQLAlchemy metadata so the models
remain the single source of truth for the MVP.
"""

from alembic import op

import app.models  # noqa: F401  (register tables)
from app.core.database import Base

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
