from collections import defaultdict
from io import BytesIO
import mimetypes
import os
import re
from typing import Dict, Iterable, List
from urllib.parse import unquote, urlparse
from urllib.request import urlopen

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from pypdf import PdfReader, PdfWriter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import MINIO_ACCESS_KEY, MINIO_BUCKET_NAME, MINIO_REGION, MINIO_SECRET_KEY, MINIO_URL, MINIO_URL_SERT
from app.exceptions import BadRequestException, DatabaseException, NotFoundException
from app.models.file import File
from app.models.topic import Topic, TopicTag
from app.schemas.file import FileCreate
from app.crud.file import create_file

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_URL,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name=MINIO_REGION,
)


def _extract_minio_key(file_path: str) -> str:
    if not file_path:
        raise BadRequestException("Не указан путь к файлу")
    parsed = urlparse(file_path)
    path = unquote(parsed.path or "").lstrip("/")
    if path.startswith(f"{MINIO_BUCKET_NAME}/"):
        return path[len(MINIO_BUCKET_NAME) + 1:]
    if parsed.scheme:
        return path
    if file_path.startswith(f"{MINIO_BUCKET_NAME}/"):
        return file_path[len(MINIO_BUCKET_NAME) + 1:]
    return file_path


def download_file_from_minio(file: File) -> bytes:
    if not file:
        raise BadRequestException("Файл для разделения не найден")
    if file.provider and file.provider != "minio":
        raise BadRequestException("Файл должен храниться в MinIO")
    key = _extract_minio_key(file.path)
    if not key:
        raise BadRequestException("Некорректный путь к файлу в MinIO")
    try:
        response = s3.get_object(Bucket=MINIO_BUCKET_NAME, Key=key)
    except ClientError as exc:
        raise DatabaseException(f"Ошибка при получении файла: {str(exc)}") from exc
    body = response.get("Body")
    if not body:
        raise BadRequestException("Не удалось получить содержимое файла")
    return body.read()


def download_file_from_link(file_link: str) -> tuple[bytes, str, str]:
    if not file_link:
        raise BadRequestException("Не указана ссылка на файл")
    filename = unquote(urlparse(file_link).path.split("/")[-1] or "")
    if not filename:
        raise BadRequestException("Не удалось определить имя файла")
    content_type = mimetypes.guess_type(filename)[0] or "application/pdf"
    key = _extract_minio_key(file_link)
    if key:
        try:
            response = s3.get_object(Bucket=MINIO_BUCKET_NAME, Key=key)
            body = response.get("Body")
            if body:
                return body.read(), filename, content_type
        except ClientError:
            pass
    try:
        with urlopen(file_link) as response:
            return response.read(), filename, content_type
    except Exception as exc:
        raise BadRequestException("Не удалось получить содержимое файла по ссылке") from exc


async def _get_or_create_topic(db: AsyncSession, name: str) -> Topic:
    stmt = (
        select(Topic)
        .options(selectinload(Topic.files), selectinload(Topic.tags))
        .where(func.lower(Topic.name) == name.lower())
    )
    result = await db.execute(stmt)
    topic = result.scalar_one_or_none()
    if topic:
        return topic
    topic = Topic(name=name)
    db.add(topic)
    await db.flush()
    return topic


async def _get_or_create_tags(db: AsyncSession, tag_names: List[str]) -> List[TopicTag]:
    unique = {tag.strip() for tag in tag_names if tag and tag.strip()}
    if not unique:
        return []
    stmt = select(TopicTag).where(func.lower(TopicTag.name).in_({tag.lower() for tag in unique}))
    result = await db.execute(stmt)
    existing = {tag.name.lower(): tag for tag in result.scalars().all()}
    tags: List[TopicTag] = []
    for name in unique:
        key = name.lower()
        tag = existing.get(key)
        if not tag:
            tag = TopicTag(name=name)
            db.add(tag)
            await db.flush()
        tags.append(tag)
    return tags


def _parse_range_tokens(tokens: Iterable[str]) -> List[int]:
    pages: List[int] = []
    for token in tokens:
        part = token.strip()
        if not part:
            continue
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start = int(start_str)
            end = int(end_str)
            if start < 1 or end < 1 or start > end:
                raise BadRequestException(f"Некорректный диапазон страниц: {part}")
            pages.extend(range(start, end + 1))
        else:
            page = int(part)
            if page < 1:
                raise BadRequestException(f"Некорректный номер страницы: {part}")
            pages.append(page)
    return pages


def _pages_from_value(value: object) -> List[int]:
    if isinstance(value, list):
        pages: List[int] = []
        for item in value:
            pages.extend(_pages_from_value(item))
        return pages
    if isinstance(value, str):
        tokens = value.split(",")
        return _parse_range_tokens(tokens)
    if isinstance(value, int):
        if value < 1:
            raise BadRequestException(f"Некорректный номер страницы: {value}")
        return [value]
    raise BadRequestException("Некорректный формат диапазона страниц")


def _group_pages_by_topic(page_topic_map: Dict) -> Dict[str, List[int]]:
    grouped: Dict[str, List[int]] = defaultdict(list)
    for topic_name, ranges in page_topic_map.items():
        if not topic_name:
            raise BadRequestException("Имя темы не может быть пустым")
        if isinstance(topic_name, int) or str(topic_name).isdigit():
            raise BadRequestException("Ключи page_topic_map должны быть названиями тем")
        pages = _pages_from_value(ranges)
        grouped[str(topic_name)].extend(pages)
    return grouped


def _sanitize_filename_part(value: str, fallback: str) -> str:
    cleaned = re.sub(r"\s+", " ", value or "").strip()
    cleaned = cleaned.replace("/", "_").replace("\\", "_")
    return cleaned or fallback


def _sanitize_topic_filename(topic_name: str) -> str:
    return _sanitize_filename_part(topic_name, "topic")


def _build_topic_filename(source_filename: str, topic_name: str) -> str:
    source_base = os.path.splitext(source_filename or "")[0]
    source_part = _sanitize_filename_part(source_base, "source")
    topic_part = _sanitize_filename_part(topic_name, "topic")
    parts = [source_part]
    if topic_part and topic_part.lower() not in source_part.lower():
        parts.append(topic_part)
    return "_".join(parts)


def _truncate_filename(filename: str, max_length: int = 120) -> str:
    if not filename or len(filename) <= max_length:
        return filename
    base, extension = os.path.splitext(filename)
    if len(extension) >= max_length:
        return filename[:max_length]
    allowed_base_length = max_length - len(extension)
    return f"{base[:allowed_base_length]}{extension}"


def _parse_table_of_contents_line(line: str) -> tuple[str, str] | None:
    cleaned = re.sub(r"\.{2,}", " ", line or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return None
    if re.search(r"\bсодержание\b", cleaned, re.IGNORECASE):
        return None
    match = re.search(
        r"^(?P<title>.+?)\s+(?P<pages>\d+(?:\s*[-–—]\s*\d+)?(?:\s*,\s*\d+(?:\s*[-–—]\s*\d+)?)*)\s*$",
        cleaned,
    )
    if not match:
        return None
    title = match.group("title").strip(" .-—–")
    pages = match.group("pages")
    if not title or not pages:
        return None
    pages = re.sub(r"\s*[-–—]\s*", "-", pages)
    pages = re.sub(r"\s*,\s*", ", ", pages)
    return title, pages


def extract_table_of_contents_from_pdf(book_pdf: bytes) -> Dict[str, str]:
    if not book_pdf:
        raise BadRequestException("Файл пустой")
    reader = PdfReader(BytesIO(book_pdf))
    pages_text = [(page.extract_text() or "") for page in reader.pages]
    toc_index = next(
        (index for index, text in enumerate(pages_text) if re.search(r"\bсодержание\b", text, re.IGNORECASE)),
        None,
    )
    if toc_index is None:
        return {}
    results: Dict[str, str] = {}
    empty_pages = 0
    for text in pages_text[toc_index:]:
        lines = text.splitlines()
        page_matches = 0
        for line in lines:
            parsed = _parse_table_of_contents_line(line)
            if not parsed:
                continue
            title, pages = parsed
            results.setdefault(title, pages)
            page_matches += 1
        if results and page_matches == 0:
            empty_pages += 1
            if empty_pages >= 2:
                break
        else:
            empty_pages = 0
    return results


async def split_book_by_topics(
    db: AsyncSession,
    creator_id: int,
    book_pdf: bytes,
    filename: str,
    content_type: str,
    page_topic_map: Dict,
) -> List[Topic]:
    if not page_topic_map:
        raise BadRequestException("page_topic_map не может быть пустым")

    reader = PdfReader(BytesIO(book_pdf))
    total_pages = len(reader.pages)
    grouped = _group_pages_by_topic(page_topic_map)
    topics: List[Topic] = []

    for topic_name, pages in grouped.items():
        writer = PdfWriter()
        for page_number in sorted(pages):
            if page_number < 1 or page_number > total_pages:
                raise BadRequestException(f"Недопустимый номер страницы: {page_number}")
            writer.add_page(reader.pages[page_number - 1])
        buffer = BytesIO()
        writer.write(buffer)
        content = buffer.getvalue()
        topic = await _get_or_create_topic(db, topic_name)
        await db.refresh(topic, attribute_names=["tags"])
        extension = os.path.splitext(filename)[1] if filename else ".pdf"
        tags = await _get_or_create_tags(db, [topic_name])
        topic_filename = f"{_build_topic_filename(filename, topic_name)}{extension}"
        topic_filename = _truncate_filename(topic_filename)
        key = f"user_{creator_id}/topics/{topic.id}/{topic_filename}"
        try:
            s3.put_object(
                Bucket=MINIO_BUCKET_NAME,
                Key=key,
                Body=content,
                ContentLength=len(content),
                ContentType=content_type,
            )
        except ClientError as exc:
            raise DatabaseException(f"Ошибка при загрузке файла: {str(exc)}") from exc

        url = f"{MINIO_URL_SERT}/{MINIO_BUCKET_NAME}/{key}"
        file_row = await create_file(
            db,
            FileCreate(
                type=content_type,
                name=key.split("/")[-1],
                size=len(content),
                path=url,
                provider="minio",
                creator_id=creator_id,
            ),
        )

        for tag in tags:
            if tag not in topic.tags:
                topic.tags.append(tag)
        await db.refresh(topic, attribute_names=["files"])
        if file_row not in topic.files:
            topic.files.append(file_row)
        topics.append(topic)

    await db.commit()
    for topic in topics:
        await db.refresh(topic)
    return topics


async def add_tags_to_topic(db: AsyncSession, topic_id: int, tags: List[str]) -> Topic:
    result = await db.execute(
        select(Topic)
        .options(selectinload(Topic.tags), selectinload(Topic.files))
        .where(Topic.id == topic_id)
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise NotFoundException("Тема не найдена")
    new_tags = await _get_or_create_tags(db, tags)
    existing = {tag.name.lower() for tag in topic.tags}
    for tag in new_tags:
        if tag.name.lower() not in existing:
            topic.tags.append(tag)
    await db.commit()
    await db.refresh(topic)
    return topic


async def search_documents_by_tags(db: AsyncSession, tags: List[str]) -> List[Topic]:
    if not tags:
        raise BadRequestException("Не указаны теги для поиска")
    normalized = [tag.strip().lower() for tag in tags if tag and tag.strip()]
    if not normalized:
        raise BadRequestException("Не указаны теги для поиска")

    stmt = (
        select(Topic)
        .join(Topic.tags)
        .options(selectinload(Topic.tags), selectinload(Topic.files))
        .where(func.lower(TopicTag.name).in_(normalized))
        .group_by(Topic.id)
        .having(func.count(func.distinct(TopicTag.id)) == len(set(normalized)))
    )
    result = await db.execute(stmt)
    return result.scalars().all()
