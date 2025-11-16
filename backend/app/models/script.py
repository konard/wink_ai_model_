from typing import Optional
from datetime import datetime
from sqlalchemy import (
    Integer,
    String,
    Text,
    Float,
    DateTime,
    JSON,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from ..db.base import Base


class Script(Base):  # type: ignore[misc, valid-type]
    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_rating: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    agg_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    total_scenes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    scenes = relationship(
        "Scene", back_populates="script", cascade="all, delete-orphan"
    )
    ratings = relationship(
        "RatingLog", back_populates="script", cascade="all, delete-orphan"
    )
    versions = relationship(
        "ScriptVersion", back_populates="script", cascade="all, delete-orphan"
    )


class Scene(Base):  # type: ignore[misc, valid-type]
    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    script_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False
    )
    scene_id: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str] = mapped_column(String(500), nullable=False)
    sample_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    violence: Mapped[float] = mapped_column(Float, default=0.0)
    gore: Mapped[float] = mapped_column(Float, default=0.0)
    sex_act: Mapped[float] = mapped_column(Float, default=0.0)
    nudity: Mapped[float] = mapped_column(Float, default=0.0)
    profanity: Mapped[float] = mapped_column(Float, default=0.0)
    drugs: Mapped[float] = mapped_column(Float, default=0.0)
    child_risk: Mapped[float] = mapped_column(Float, default=0.0)
    weight: Mapped[float] = mapped_column(Float, default=0.0)

    script = relationship("Script", back_populates="scenes")


class RatingLog(Base):  # type: ignore[misc, valid-type]
    __tablename__ = "rating_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    script_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False
    )
    predicted_rating: Mapped[str] = mapped_column(String(10), nullable=False)
    reasons: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    script = relationship("Script", back_populates="ratings")


class ScriptVersion(Base):  # type: ignore[misc, valid-type]
    __tablename__ = "script_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    script_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_rating: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    agg_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    total_scenes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    change_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    scenes_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    version_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    script = relationship("Script", back_populates="versions")
