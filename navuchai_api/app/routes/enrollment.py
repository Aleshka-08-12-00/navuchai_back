from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.crud import (
    enroll_user,
    unenroll_user,
    get_user_courses,
    get_all_user_courses,
    authorized_required,
    get_current_user,
    admin_moderator_required,
)
from app.models import User
from app.schemas.course_enrollment import CourseEnrollmentBase

router = APIRouter(prefix="/api/courses", tags=["Enrollment"])


@router.post("/{course_id}/enroll/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(authorized_required)])
async def enroll(course_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await enroll_user(db, course_id, user.id)


@router.post("/{course_id}/enroll/{user_id}/", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[Depends(admin_moderator_required)])
async def enroll_user_admin(course_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    await enroll_user(db, course_id, user_id)


@router.delete("/{course_id}/enroll/{user_id}/", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(admin_moderator_required)])
async def unenroll(course_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    await unenroll_user(db, course_id, user_id)


@router.get("/users/{user_id}/courses/")
async def user_courses(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_user_courses(db, user_id)


@router.get(
    "/users/courses/",
    response_model=list[CourseEnrollmentBase],
    dependencies=[Depends(admin_moderator_required)],
)
async def all_user_courses(db: AsyncSession = Depends(get_db)):
    return await get_all_user_courses(db)
