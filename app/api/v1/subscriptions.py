import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_tenant_id
from app.core.db import get_session
from app.models.enums import UserRole
from app.models.subscription import Subscription
from app.schemas.subscription import ChangeTariffRequest, SubscriptionRead
from app.services import subscription as subscription_service
from app.services.errors import NotFoundError

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

tenant_admin = require_tenant_id(UserRole.TENANT_ADMIN)


@router.get("/current", response_model=SubscriptionRead)
async def get_current_subscription(
    tenant_id: uuid.UUID = Depends(tenant_admin),
    session: AsyncSession = Depends(get_session),
) -> Subscription:
    try:
        return await subscription_service.get_current_subscription(session, tenant_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None


@router.post("/change", response_model=SubscriptionRead)
async def change_tariff(
    payload: ChangeTariffRequest,
    tenant_id: uuid.UUID = Depends(tenant_admin),
    session: AsyncSession = Depends(get_session),
) -> Subscription:
    try:
        return await subscription_service.change_tariff(
            session, tenant_id, tariff_code=payload.tariff_code
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None
