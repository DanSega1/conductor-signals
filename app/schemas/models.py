from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Observation(BaseModel):
    id: str = Field(description="Unique identifier for the observation")
    timestamp: datetime = Field(description="When the observation occurred")
    source: str = Field(description="Data source name (e.g. fitbit, calendar)")
    category: str = Field(description="Category of observation (e.g. health, activity)")
    entity: str = Field(description="Specific entity being observed (e.g. sleep, steps)")
    features: dict[str, Any] = Field(
        default_factory=dict, description="Numeric/categorical feature values"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )
    version: int = Field(default=1, description="Schema version of this observation")


class ObservationCreate(BaseModel):
    timestamp: datetime
    source: str
    category: str
    entity: str
    features: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Feature(BaseModel):
    name: str = Field(description="Feature name (e.g. hrv, sleep_score)")
    value: float | str | bool = Field(description="Feature value")
    observation_id: str = Field(description="ID of the source observation")
    source: str = Field(description="Data source")
    timestamp: datetime = Field(description="When the observation occurred")


class Insight(BaseModel):
    id: str = Field(description="Unique identifier for the insight")
    title: str = Field(description="Short human-readable title")
    description: str = Field(description="Detailed explanation")
    source: str = Field(description="What generated this insight")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    timestamp: datetime = Field(description="When the insight was generated")
    metadata: dict[str, Any] = Field(default_factory=dict)
