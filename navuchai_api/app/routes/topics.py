import json
from typing import List

from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import authorized_required, get_current_user, root_admin_moderator_required
from app.crud.lesson import get_lesson
from app.dependencies import get_db
from app.exceptions import BadRequestException
from app.models import User
from app.schemas.topic import TopicResponse, TopicSearchRequest, TopicSplitRequest, TopicTagsUpdateRequest
from app.crud import topic as topic_crud

router = APIRouter(prefix="/api/topics", tags=["Topics"])


@router.post(
    "/split/",
    response_model=List[TopicResponse],
    dependencies=[Depends(root_admin_moderator_required)],
)
async def split_book_by_topics(
    page_topic_map: str = Form(..., alias="pageTopicMap"),
    lesson_id: int = Form(..., alias="lessonId"),
    file_id: int | None = Form(None, alias="fileId"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lesson = await get_lesson(db, lesson_id)
    if not lesson.files:
        raise BadRequestException("В уроке нет файлов для разделения")
    file = None
    if file_id is not None:
        file = next((item for item in lesson.files if item.id == file_id), None)
        if not file:
            raise BadRequestException("Файл для разделения не найден в уроке")
    else:
        file = lesson.files[0]
    content = topic_crud.download_file_from_minio(file)
    payload = json.loads(page_topic_map)
    request = TopicSplitRequest(pageTopicMap=payload)
    topics = await topic_crud.split_book_by_topics(
        db,
        user.id,
        content,
        file.name,
        file.type or "application/pdf",
        request.page_topic_map,
    )
    return [TopicResponse.model_validate(topic, from_attributes=True) for topic in topics]


@router.post(
    "/{topic_id}/tags/",
    response_model=TopicResponse,
    dependencies=[Depends(root_admin_moderator_required)],
)
async def add_tags(
    topic_id: int,
    data: TopicTagsUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    topic = await topic_crud.add_tags_to_topic(db, topic_id, data.tags)
    return TopicResponse.model_validate(topic, from_attributes=True)


@router.post(
    "/search/",
    response_model=List[TopicResponse],
    dependencies=[Depends(authorized_required)],
)
async def search_by_tags(
    data: TopicSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    topics = await topic_crud.search_documents_by_tags(db, data.tags)
    return [TopicResponse.model_validate(topic, from_attributes=True) for topic in topics]
