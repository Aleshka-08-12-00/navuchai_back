from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.crud import get_user_calendar, authorized_required
from app.schemas.calendar import CalendarSimpleEvent
from app.models import User


router = APIRouter(prefix="/api/calendar", tags=["Calendar"])


@router.get("/my/", response_model=list[CalendarSimpleEvent])
async def get_my_calendar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    try:
        events = await get_user_calendar(db, current_user.id)
        simplified = []
        type_to_ru = {
            "test_access_start": "Тест",
            "test_access_end": "Тест",
            "test_group_start": "Группа тестов",
            "test_group_end": "Группа тестов",
            "course_enrolled": "Курс",
            "adaptation_assigned": "Адаптация",
            "adaptation_deadline": "Адаптация",
            "adaptation_completed": "Адаптация",
        }
        for e in events:
            etype = e.get("type")
            title = e.get("title")
            start = e.get("start")
            end = e.get("end")
            if not start:
                continue
            ru_type = type_to_ru.get(etype, "Событие")
            name = f"{ru_type}: {title}" if title else ru_type
            simplified.append(CalendarSimpleEvent(name=name, start=start, end=end))
        return simplified
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении календаря: {str(e)}")


