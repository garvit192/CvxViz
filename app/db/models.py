from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Float, Integer, ForeignKey, Index
from datetime import datetime
from .session import Base
import uuid

def _uuid() -> str: return str(uuid.uuid4())

class Problem(Base):
    __tablename__ = "problems"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    spec_hash: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

Index("ix_problems_spec_hash_created", Problem.spec_hash, Problem.created_at.desc())

class Solution(Base):
    __tablename__ = "solutions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    problem_id: Mapped[str] = mapped_column(String(36), ForeignKey("problems.id"), index=True)
    status: Mapped[str] = mapped_column(String(32))
    objective_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    solution_json: Mapped[str] = mapped_column(Text)
    duration_ms: Mapped[int] = mapped_column(Integer)
    cached: Mapped[int] = mapped_column(Integer, default=0)  # bool as 0/1
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
