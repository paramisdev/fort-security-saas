import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SubscriptionStatus
from app.schemas.tariff import TariffRead


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    tariff: TariffRead
    status: SubscriptionStatus
    period_started_at: datetime
    period_expires_at: datetime | None


class ChangeTariffRequest(BaseModel):
    tariff_code: str = Field(min_length=2, max_length=50)
