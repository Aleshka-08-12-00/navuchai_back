from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
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
    get_course_test,
    delete_course_test,
    get_current_user_optional,
    get_last_course_and_lesson,
    get_course_students_count,
    get_course_lessons_count,
    set_course_rating,
    get_course_avg_rating,
)
from app.schemas.course import CourseCreate, CourseResponse, CourseWithDetails, CourseRead, ListCoursesResponse
from app.schemas.course_rating import CourseRatingCreate
from app.schemas.course_test import CourseTestBase, CourseTestCreate
from app.schemas.test import TestResponse
from app.schemas.module import ModuleWithLessons, ModuleCreate, ModuleResponse
from app.exceptions import NotFoundException, DatabaseException
from app.models import User
from app.crud import authorized_required

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get("/", response_model=dict)
async def list_courses(
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    courses_raw = await get_courses(db, user.id if user else None)

    courses: list[CourseRead] = []
    for data in courses_raw:
        course = CourseRead.model_validate(data, from_attributes=True)
        cid = course.id
        course.lessons_count = await get_course_lessons_count(db, cid)
        course.students_count = await get_course_students_count(db, cid)
        course.rating = await get_course_avg_rating(db, cid)

        if user:
            progress = await get_course_progress(db, cid, user.id)
            course.progress = progress
            course.done = progress == 100
            course.enrolled = (
                True if user.role.code == "admin" else await user_enrolled(db, cid, user.id)
            )

        courses.append(course)

    current: CourseRead | None = None
    if user:
        course_obj, _ = await get_last_course_and_lesson(db, user.id)
        if course_obj:
            cid = course_obj.id
            course_obj.enrolled = await user_enrolled(db, cid, user.id)
            progress = await get_course_progress(db, cid, user.id)
            course_obj.progress = progress
            course_obj.done = progress == 100
            course_obj.lessons_count = await get_course_lessons_count(db, cid)
            course_obj.students_count = await get_course_students_count(db, cid)
            course_obj.rating = await get_course_avg_rating(db, cid)
            current = CourseRead.model_validate(course_obj, from_attributes=True)

    return {"current": current, "courses": courses}


@router.get(
    "/{id}/",
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
    lessons_count = await get_course_lessons_count(db, id)
    students_count = await get_course_students_count(db, id)
    rating = await get_course_avg_rating(db, id)
    progress = await get_course_progress(db, id, user.id)
    done = progress == 100
    if user.role.code == "admin":
        enrolled = True
    else:
        enrolled = await user_enrolled(db, id, user.id)
    course_data = CourseRead.model_validate(course, from_attributes=True)
    course_data.lessons_count = lessons_count
    course_data.progress = progress
    course_data.done = done
    course_data.students_count = students_count
    course_data.rating = rating
    course_data.enrolled = enrolled
    return course_data


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(admin_moderator_required)])
async def create(course: CourseCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await create_course(db, course, user.id)


@router.put("/{course_id}/", response_model=CourseResponse, dependencies=[Depends(admin_moderator_required)])
async def update(course_id: int, data: CourseCreate, db: AsyncSession = Depends(get_db)):
    return await update_course(db, course_id, data)
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
    resp.rating = 0.0
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
    resp.rating = await get_course_avg_rating(db, resp.id)
    return resp


@router.delete("/{course_id}/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(admin_moderator_required)])
async def remove(course_id: int, db: AsyncSession = Depends(get_db)):
    await delete_course(db, course_id)


@router.get("/{course_id}/modules/", response_model=list[ModuleWithLessons], dependencies=[Depends(authorized_required)])
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


@router.post("/{course_id}/modules/", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module_route(course_id: int, data: ModuleCreate, db: AsyncSession = Depends(get_db)):
    return await create_module_for_course(db, course_id, data)


@router.get("/{course_id}/progress/", dependencies=[Depends(authorized_required)])
async def course_progress(course_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role.code not in ["admin", "moderator"] and not await user_enrolled(db, course_id, user.id):
        raise HTTPException(status_code=403, detail="Нет доступа к курсу")
    percent = await get_course_progress(db, course_id, user.id)
    return {"percent": percent}


@router.post("/{course_id}/rating/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(authorized_required)])
async def add_course_rating_route(
    course_id: int,
    data: CourseRatingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await set_course_rating(db, course_id, user.id, data.rating)


@router.post("/{course_id}/tests/", response_model=CourseTestBase, dependencies=[Depends(admin_moderator_required)])
async def create_course_test_route(course_id: int, data: CourseTestCreate, db: AsyncSession = Depends(get_db)):
    data.course_id = course_id
    return await create_course_test(db, data)


@router.get("/{course_id}/tests/", response_model=list[TestResponse], dependencies=[Depends(authorized_required)])
async def list_course_tests_route(course_id: int, db: AsyncSession = Depends(get_db),
                                  user: User = Depends(get_current_user)):
    if user.role.code not in ["admin", "moderator"] and not await user_enrolled(db, course_id, user.id):
        raise HTTPException(status_code=403, detail="Нет доступа к курсу")
    progress = await get_course_progress(db, course_id, user.id)
    if user.role.code not in ["admin", "moderator"] and progress < 100:
        raise HTTPException(status_code=403, detail="Курс не завершен")
    tests = await get_course_tests(db, course_id)
    return [t.test for t in tests]


@router.get("/{course_id}/tests/{test_id}/", response_model=TestResponse, dependencies=[Depends(authorized_required)])
async def get_course_test_route(
    course_id: int,
    test_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role.code not in ["admin", "moderator"] and not await user_enrolled(db, course_id, user.id):
        raise HTTPException(status_code=403, detail="Нет доступа к курсу")
    progress = await get_course_progress(db, course_id, user.id)
    if user.role.code not in ["admin", "moderator"] and progress < 100:
        raise HTTPException(status_code=403, detail="Курс не завершен")
    course_test = await get_course_test(db, course_id, test_id)
    if not course_test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    return course_test.test


@router.delete("/{course_id}/tests/{test_id}/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(admin_moderator_required)])
async def delete_course_test_route(course_id: int, test_id: int, db: AsyncSession = Depends(get_db)):
    course_test = await delete_course_test(db, course_id, test_id)
    if not course_test:
        raise HTTPException(status_code=404, detail="Тест не найден")
