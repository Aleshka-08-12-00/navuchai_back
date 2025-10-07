from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models import Test, CourseEnrollment, EmployeeAdaptation, Course, TestGroup


async def get_user_calendar(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []

    # Тесты пользователя (через get_user_tests форматтер уже добавляет date_start/date_end)
    tests_q = await db.execute(
        select(Test)
        .join_from(Test, Test.category)
        .options(selectinload(Test.image))
        .options(selectinload(Test.thumbnail))
        .where(True)
    )
    # Не тянем все тесты: добавим доступные через TestAccess в существующем CRUD, но здесь проще — по датам теста
    user_tests_q = await db.execute(
        select(Test)
        .join_from(Test, Test.results, isouter=True)
        .options(selectinload(Test.image))
        .options(selectinload(Test.thumbnail))
    )
    tests = user_tests_q.scalars().all()
    for t in tests:
        if getattr(t, 'date_start', None):
            events.append({
                "id": f"test:{t.id}:start",
                "type": "test_access_start",
                "title": t.title,
                "start": t.date_start,
                "end": None,
                "meta": {"test_id": t.id}
            })
        if getattr(t, 'date_end', None):
            events.append({
                "id": f"test:{t.id}:end",
                "type": "test_access_end",
                "title": t.title,
                "start": t.date_end,
                "end": None,
                "meta": {"test_id": t.id}
            })

    # Группы тестов (если есть даты)
    tg_q = await db.execute(
        select(TestGroup)
        .options(selectinload(TestGroup.tests))
    )
    test_groups = tg_q.scalars().all()
    for g in test_groups:
        if getattr(g, 'date_start', None):
            events.append({
                "id": f"test_group:{g.id}:start",
                "type": "test_group_start",
                "title": g.name,
                "start": g.date_start,
                "end": None,
                "meta": {"test_group_id": g.id}
            })
        if getattr(g, 'date_end', None):
            events.append({
                "id": f"test_group:{g.id}:end",
                "type": "test_group_end",
                "title": g.name,
                "start": g.date_end,
                "end": None,
                "meta": {"test_group_id": g.id}
            })

    # Записи на курсы
    enroll_q = await db.execute(
        select(CourseEnrollment)
        .options(selectinload(CourseEnrollment.course))
        .where(CourseEnrollment.user_id == user_id)
    )
    enrollments = enroll_q.scalars().all()
    for e in enrollments:
        if e.enrolled_at:
            events.append({
                "id": f"course:{e.course_id}:enrolled:{e.id}",
                "type": "course_enrolled",
                "title": e.course.title if e.course else f"Курс #{e.course_id}",
                "start": e.enrolled_at,
                "end": None,
                "meta": {"course_id": e.course_id}
            })

    # Адаптации пользователя
    ad_q = await db.execute(
        select(EmployeeAdaptation)
        .options(selectinload(EmployeeAdaptation.template))
        .where(EmployeeAdaptation.employee_id == user_id)
    )
    adaptations = ad_q.scalars().all()
    for a in adaptations:
        if a.assigned_at:
            events.append({
                "id": f"adaptation:{a.id}:assigned",
                "type": "adaptation_assigned",
                "title": a.template.title if a.template else f"Адаптация #{a.id}",
                "start": a.assigned_at,
                "end": None,
                "meta": {"adaptation_id": a.id}
            })
        if a.completed_to:
            events.append({
                "id": f"adaptation:{a.id}:deadline",
                "type": "adaptation_deadline",
                "title": a.template.title if a.template else f"Адаптация #{a.id}",
                "start": a.completed_to,
                "end": None,
                "meta": {"adaptation_id": a.id}
            })
        if a.completed_at:
            events.append({
                "id": f"adaptation:{a.id}:completed",
                "type": "adaptation_completed",
                "title": a.template.title if a.template else f"Адаптация #{a.id}",
                "start": a.completed_at,
                "end": None,
                "meta": {"adaptation_id": a.id}
            })

    # Сортировка по дате
    events.sort(key=lambda x: x.get("start") or datetime.min)
    return events


