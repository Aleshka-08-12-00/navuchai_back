from typing import Any, Dict, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_activity import UserActivityCreate
from app.crud.user_activity import create_user_activity
from app.utils.activity_actions import ALLOWED_ACTIONS, ACTION_RU_NAMES


async def log_user_activity(
    db: AsyncSession,
    *,
    user_id: Optional[int],
    action: str,
    context: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    # Простая валидация кода действия
    if action not in ALLOWED_ACTIONS:
        # Не прерываем основной поток: можно либо игнорировать, либо всё равно записать.
        # Здесь выбрано — всё равно записать, чтобы не потерять событие, но можно включить строгий режим.
        pass
    ip = None
    user_agent = None
    if request is not None:
        ip = request.client.host if request and request.client else None
        user_agent = request.headers.get("user-agent") if request else None
    data = UserActivityCreate(
        user_id=user_id,
        action=action,
        action_ru=ACTION_RU_NAMES.get(action),
        context=context,
        ip=ip,
        user_agent=user_agent,
    )
    await create_user_activity(db, data)


