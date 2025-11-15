"""Add script versioning system

Revision ID: 002
Revises: 001
Create Date: 2025-01-15 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scripts", sa.Column("current_version", sa.Integer(), nullable=True))
    op.execute("UPDATE scripts SET current_version = 1 WHERE current_version IS NULL")
    op.alter_column("scripts", "current_version", nullable=False, server_default="1")

    op.create_table(
        "script_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("predicted_rating", sa.String(length=10), nullable=True),
        sa.Column("agg_scores", sa.JSON(), nullable=True),
        sa.Column("total_scenes", sa.Integer(), nullable=True),
        sa.Column("change_description", sa.Text(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("scenes_data", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_script_versions_id"), "script_versions", ["id"], unique=False
    )
    op.create_index(
        "ix_script_versions_script_id", "script_versions", ["script_id"], unique=False
    )
    op.create_index(
        "ix_script_versions_version_number",
        "script_versions",
        ["version_number"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_script_versions_version_number", table_name="script_versions")
    op.drop_index("ix_script_versions_script_id", table_name="script_versions")
    op.drop_index(op.f("ix_script_versions_id"), table_name="script_versions")
    op.drop_table("script_versions")
    op.drop_column("scripts", "current_version")
