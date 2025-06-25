from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.dependencies import get_db
from app.crud import (
    get_courses,
    get_course,
    create_course,
    update_course,
    delete_course,
    get_current_user,
    admin_moderator_required,
    get_course_with_content,
    get_modules_by_course,
    get_lessons_by_module,
    create_module_for_course,
    get_course_progress,
    user_enrolled,
    create_course_test,
    get_course_tests,
)
from app.schemas.course import CourseCreate, CourseResponse, CourseWithDetails, CourseRead
from app.schemas.course_test import CourseTestBase, CourseTestCreate
from app.schemas.test import TestResponse
from app.schemas.module import ModuleWithLessons, ModuleCreate, ModuleResponse
from app.exceptions import NotFoundException, DatabaseException
from app.models import User, LessonProgress
from app.crud import authorized_required

router = APIRouter(prefix="/api/courses", tags=["Courses"])

@router.get("/", response_model=list[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db)):
    return await get_courses(db)

@router.get("/{id}", response_model=CourseRead, dependencies=[Depends(authorized_required)])
async def read_course(id: int, db=Depends(get_db), user: User = Depends(get_current_user)):
    course = await get_course_with_content(db, id)
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    if user.role.code not in ["admin", "moderator"] and not await user_enrolled(db, id, user.id):
        raise HTTPException(status_code=403, detail="Нет доступа к курсу")
    lesson_ids = [l.id for m in course.modules for l in m.lessons]
    if lesson_ids:
        res = await db.execute(
            select(LessonProgress.lesson_id).where(
                LessonProgress.user_id == user.id,
                LessonProgress.lesson_id.in_(lesson_ids),
            )
        )
        completed_ids = {row[0] for row in res.all()}
        for m in course.modules:
            for l in m.lessons:
                l.completed = l.id in completed_ids
    return course

@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(admin_moderator_required)])
async def create(course: CourseCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await create_course(db, course, user.id)

@router.put("/{course_id}", response_model=CourseResponse, dependencies=[Depends(admin_moderator_required)])
async def update(course_id: int, data: CourseCreate, db: AsyncSession = Depends(get_db)):
    return await update_course(db, course_id, data)

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(admin_moderator_required)])
async def remove(course_id: int, db: AsyncSession = Depends(get_db)):
    await delete_course(db, course_id)

@router.get("/{course_id}/modules", response_model=list[ModuleWithLessons], dependencies=[Depends(authorized_required)])
async def list_course_modules(course_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role.code not in ["admin", "moderator"] and not await user_enrolled(db, course_id, user.id):
        raise HTTPException(status_code=403, detail="Нет доступа к курсу")
    modules = await get_modules_by_course(db, course_id)
    for module in modules:
        module.lessons = await get_lessons_by_module(db, module.id, user.id)
    if modules:
        return modules
    try:
        await get_course(db, course_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    return []

@router.post("/{course_id}/modules", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module_route(course_id: int, data: ModuleCreate, db: AsyncSession = Depends(get_db)):
    return await create_module_for_course(db, course_id, data)


@router.get("/{course_id}/progress", dependencies=[Depends(authorized_required)])
async def course_progress(course_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role.code not in ["admin", "moderator"] and not await user_enrolled(db, course_id, user.id):
        raise HTTPException(status_code=403, detail="Нет доступа к курсу")
    percent = await get_course_progress(db, course_id, user.id)
    return {"percent": percent}


@router.post("/{course_id}/tests", response_model=CourseTestBase, dependencies=[Depends(admin_moderator_required)])
async def create_course_test_route(course_id: int, data: CourseTestCreate, db: AsyncSession = Depends(get_db)):
    data.course_id = course_id
    return await create_course_test(db, data)


@router.get("/{course_id}/tests", response_model=list[TestResponse], dependencies=[Depends(authorized_required)])
async def list_course_tests_route(course_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role.code not in ["admin", "moderator"] and not await user_enrolled(db, course_id, user.id):
        raise HTTPException(status_code=403, detail="Нет доступа к курсу")
    progress = await get_course_progress(db, course_id, user.id)
    if user.role.code not in ["admin", "moderator"] and progress < 100:
        raise HTTPException(status_code=403, detail="Курс не завершен")
    tests = await get_course_tests(db, course_id)
    return [t.test for t in tests]
