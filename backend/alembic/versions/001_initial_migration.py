"""Initial migration: create scripts, scenes, and rating_logs tables

Revision ID: 001
Revises:
Create Date: 2025-11-14

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scripts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("predicted_rating", sa.String(length=10), nullable=True),
        sa.Column("agg_scores", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column("total_scenes", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scripts_id"), "scripts", ["id"], unique=False)
    op.create_index(op.f("ix_scripts_title"), "scripts", ["title"], unique=False)

    op.create_table(
        "scenes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column("scene_id", sa.Integer(), nullable=False),
        sa.Column("heading", sa.String(length=500), nullable=False),
        sa.Column("sample_text", sa.Text(), nullable=True),
        sa.Column("violence", sa.Float(), nullable=True),
        sa.Column("gore", sa.Float(), nullable=True),
        sa.Column("sex_act", sa.Float(), nullable=True),
        sa.Column("nudity", sa.Float(), nullable=True),
        sa.Column("profanity", sa.Float(), nullable=True),
        sa.Column("drugs", sa.Float(), nullable=True),
        sa.Column("child_risk", sa.Float(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scenes_id"), "scenes", ["id"], unique=False)

    op.create_table(
        "rating_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column("predicted_rating", sa.String(length=10), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rating_logs_id"), "rating_logs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_rating_logs_id"), table_name="rating_logs")
    op.drop_table("rating_logs")
    op.drop_index(op.f("ix_scenes_id"), table_name="scenes")
    op.drop_table("scenes")
    op.drop_index(op.f("ix_scripts_title"), table_name="scripts")
    op.drop_index(op.f("ix_scripts_id"), table_name="scripts")
    op.drop_table("scripts")
