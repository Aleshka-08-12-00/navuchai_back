from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.crud import set_course_rating, get_average_course_rating, authorized_required, get_current_user
from app.schemas.course_rating import CourseRatingCreate, CourseRatingBase
from app.models import User

router = APIRouter(prefix="/api/courses", tags=["Course Ratings"])


@router.post("/{course_id}/rating/", response_model=CourseRatingBase, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(authorized_required)])
async def create_or_update_rating(course_id: int, data: CourseRatingCreate,
                                  db: AsyncSession = Depends(get_db),
                                  user: User = Depends(get_current_user)):
    if not 1 <= data.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    rating = await set_course_rating(db, course_id, user.id, data.rating)
    return rating


@router.get("/{course_id}/rating/", response_model=dict)
async def get_average_rating(course_id: int, db: AsyncSession = Depends(get_db)):
    avg = await get_average_course_rating(db, course_id)
    return {"average": avg}
