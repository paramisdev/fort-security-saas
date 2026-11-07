"""Сборка роутера API v1."""

from fastapi import APIRouter

from app.api.v1 import auth, devices, objects, subscriptions, tariffs, users

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(tariffs.router)
api_v1_router.include_router(objects.router)
api_v1_router.include_router(devices.router)
api_v1_router.include_router(subscriptions.router)
