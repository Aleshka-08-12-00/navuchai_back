from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
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
    get_current_user_optional,
    get_last_course_and_lesson,
)
from app.schemas.course import CourseCreate, CourseResponse, CourseWithDetails, CourseRead
from app.schemas.lesson import LessonResponse
from app.schemas.course_test import CourseTestBase, CourseTestCreate
from app.schemas.test import TestResponse
from app.schemas.module import ModuleWithLessons, ModuleCreate, ModuleResponse
from app.exceptions import NotFoundException, DatabaseException
from app.models import User
from app.crud import authorized_required, get_course_with_content

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get("/", response_model=dict)
async def list_courses(
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    courses_raw = await get_courses(db)
    courses: list[CourseResponse] = []
    for c in courses_raw:
        course = CourseResponse.model_validate(c)
        if user:
            course.progress = await get_course_progress(db, course.id, user.id)
        courses.append(course)
    courses_raw = await get_courses(db, user.id if user else None)
    courses = [CourseResponse.model_validate(c) for c in courses_raw]
    if user:
        course_obj, lesson_obj = await get_last_course_and_lesson(db, user.id)
        if course_obj:
            setattr(course_obj, "enrolled", await user_enrolled(db, course_obj.id, user.id))
            course_current = CourseResponse.model_validate(course_obj)
            course_current.progress = await get_course_progress(
                db, course_current.id, user.id
            )
    return {"current": course_current, "courses": courses}

@router.get(
    "/{id}",
    response_model=CourseRead,
    response_model_exclude={"modules"},
)
async def read_course(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(authorized_required),
):
    course = await get_course_with_content(db, id)
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    setattr(course, "enrolled", await user_enrolled(db, id, user.id))
    return course


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(admin_moderator_required)])
async def create(course: CourseCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await create_course(db, course, user.id)

    resp = CourseRead.model_validate(course)
    resp.progress = await get_course_progress(db, resp.id, user.id)
    return resp

@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(admin_moderator_required)],
)
async def create(
    course: CourseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course_obj = await create_course(db, course, user.id)
    resp = CourseResponse.model_validate(course_obj)
    resp.progress = 0.0
    return resp

@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    dependencies=[Depends(admin_moderator_required)],
)
async def update(
    course_id: int,
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course_obj = await update_course(db, course_id, data)
    resp = CourseResponse.model_validate(course_obj)
    resp.progress = await get_course_progress(db, resp.id, user.id)
    return resp


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(admin_moderator_required)])
async def remove(course_id: int, db: AsyncSession = Depends(get_db)):
    await delete_course(db, course_id)


@router.get("/{course_id}/modules", response_model=list[ModuleWithLessons], dependencies=[Depends(authorized_required)])
async def list_course_modules(course_id: int, db: AsyncSession = Depends(get_db),
                              user: User = Depends(get_current_user)):
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
async def list_course_tests_route(course_id: int, db: AsyncSession = Depends(get_db),
                                  user: User = Depends(get_current_user)):
    if user.role.code not in ["admin", "moderator"] and not await user_enrolled(db, course_id, user.id):
        raise HTTPException(status_code=403, detail="Нет доступа к курсу")
    progress = await get_course_progress(db, course_id, user.id)
    if user.role.code not in ["admin", "moderator"] and progress < 100:
        raise HTTPException(status_code=403, detail="Курс не завершен")
    tests = await get_course_tests(db, course_id)
    return [t.test for t in tests]
