"""Rename metadata to version_metadata

Revision ID: 003
Revises: 002
Create Date: 2025-01-15 14:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("script_versions", "metadata", new_column_name="version_metadata")


def downgrade() -> None:
    op.alter_column("script_versions", "version_metadata", new_column_name="metadata")
