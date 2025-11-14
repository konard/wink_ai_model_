from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.base import Base


class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    predicted_rating = Column(String(10), nullable=True)
    agg_scores = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=True)
    total_scenes = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    scenes = relationship(
        "Scene", back_populates="script", cascade="all, delete-orphan"
    )
    ratings = relationship(
        "RatingLog", back_populates="script", cascade="all, delete-orphan"
    )


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(
        Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False
    )
    scene_id = Column(Integer, nullable=False)
    heading = Column(String(500), nullable=False)
    sample_text = Column(Text, nullable=True)

    violence = Column(Float, default=0.0)
    gore = Column(Float, default=0.0)
    sex_act = Column(Float, default=0.0)
    nudity = Column(Float, default=0.0)
    profanity = Column(Float, default=0.0)
    drugs = Column(Float, default=0.0)
    child_risk = Column(Float, default=0.0)
    weight = Column(Float, default=0.0)

    script = relationship("Script", back_populates="scenes")


class RatingLog(Base):
    __tablename__ = "rating_logs"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(
        Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False
    )
    predicted_rating = Column(String(10), nullable=False)
    reasons = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    script = relationship("Script", back_populates="ratings")
