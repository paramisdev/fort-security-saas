import asyncio
import sys

from sqlalchemy import select

from app.core import security
from app.core.db import engine, session_maker
from app.models import Base, Tariff, User
from app.models.enums import UserRole

DEFAULT_TARIFFS = [
    {
        "code": "start",
        "name": "Старт",
        "price_monthly": 990.00,
        "max_objects": 1,
        "max_devices": 3,
        "features": {"alerts": "email"},
    },
    {
        "code": "comfort",
        "name": "Комфорт",
        "price_monthly": 2490.00,
        "max_objects": 3,
        "max_devices": 10,
        "features": {"alerts": "email,sms", "reports": "monthly"},
    },
    {
        "code": "premium",
        "name": "Премиум",
        "price_monthly": 4990.00,
        "max_objects": 10,
        "max_devices": 30,
        "features": {"alerts": "email,sms,push", "reports": "weekly", "support": "priority"},
    },
    {
        "code": "premium_plus",
        "name": "Премиум+",
        "price_monthly": 9990.00,
        "max_objects": 50,
        "max_devices": 200,
        "features": {
            "alerts": "email,sms,push",
            "reports": "daily",
            "support": "dedicated",
            "white_label": True,
        },
    },
]


async def seed() -> None:
    from app.core.config import get_settings

    settings = get_settings()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        for data in DEFAULT_TARIFFS:
            existing = await session.execute(select(Tariff).where(Tariff.code == data["code"]))
            if existing.scalar_one_or_none() is None:
                session.add(Tariff(**data))
        await session.flush()

        existing_admin = await session.execute(
            select(User).where(User.email == settings.superadmin_email)
        )
        if existing_admin.scalar_one_or_none() is None:
            session.add(
                User(
                    email=settings.superadmin_email,
                    hashed_password=security.hash_password(settings.superadmin_password),
                    full_name="Super Admin",
                    role=UserRole.SUPERADMIN,
                    tenant_id=None,
                )
            )

        await session.commit()

    tariff_count = len(DEFAULT_TARIFFS)
    print(f"Seed complete: {tariff_count} tariffs ensured, superadmin ensured.")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed())
