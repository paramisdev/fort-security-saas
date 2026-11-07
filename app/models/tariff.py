from typing import Any

from sqlalchemy import JSON, Boolean, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPkMixin

# JSONB в PostgreSQL, обычный JSON в остальных СУБД (тесты на aiosqlite).
JsonType = JSON().with_variant(JSONB(), "postgresql")


class Tariff(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "tariffs"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    price_monthly: Mapped[float] = mapped_column(Numeric(10, 2))
    max_objects: Mapped[int] = mapped_column(Integer)
    max_devices: Mapped[int] = mapped_column(Integer)
    features: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
