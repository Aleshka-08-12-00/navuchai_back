import json
from typing import List

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import authorized_required, get_current_user, root_admin_moderator_required
from app.dependencies import get_db
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
    file: UploadFile = File(...),
    page_topic_map: str = Form(..., alias="pageTopicMap"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await file.read()
    payload = json.loads(page_topic_map)
    request = TopicSplitRequest(pageTopicMap=payload)
    topics = await topic_crud.split_book_by_topics(
        db,
        user.id,
        content,
        file.filename,
        file.content_type or "application/pdf",
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
