import uuid

from sqlalchemy import func, select

from app.models.device import Device
from app.models.enums import DeviceStatus, DeviceType
from app.repositories.base import BaseRepository


class DeviceRepository(BaseRepository[Device]):
    model = Device

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        object_id: uuid.UUID | None = None,
        device_type: DeviceType | None = None,
        status: DeviceStatus | None = None,
    ) -> list[Device]:
        query = select(Device).where(Device.tenant_id == tenant_id)
        if object_id is not None:
            query = query.where(Device.object_id == object_id)
        if device_type is not None:
            query = query.where(Device.type == device_type)
        if status is not None:
            query = query.where(Device.status == status)
        result = await self.session.execute(query.order_by(Device.created_at))
        return list(result.scalars().all())

    async def get_in_tenant(self, device_id: uuid.UUID, tenant_id: uuid.UUID) -> Device | None:
        result = await self.session.execute(
            select(Device).where(Device.id == device_id, Device.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_serial_in_tenant(
        self, tenant_id: uuid.UUID, serial_number: str
    ) -> Device | None:
        result = await self.session.execute(
            select(Device).where(
                Device.tenant_id == tenant_id, Device.serial_number == serial_number
            )
        )
        return result.scalar_one_or_none()

    async def count_by_tenant(self, tenant_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Device).where(Device.tenant_id == tenant_id)
        )
        return int(result.scalar_one())
