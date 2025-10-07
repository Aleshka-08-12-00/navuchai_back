from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.document import Document
from app.models.folder import Folder
from app.exceptions import NotFoundException
from .folder import get_folder_shallow

async def get_document(db: AsyncSession, doc_id: int) -> Document:
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.folder))
        .where(Document.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise NotFoundException("Файл не найден")
    return doc

async def list_documents(db: AsyncSession, folder_id: Optional[int], q: Optional[str], type_: Optional[str], skip: int, limit: int) -> List[Document]:
    stmt = select(Document).order_by(Document.id)
    if folder_id is not None:
        stmt = stmt.where(Document.folder_id == folder_id)
    if q:
        stmt = stmt.where(func.lower(Document.name).like(f"%{q.lower()}%"))
    if type_:
        stmt = stmt.where(func.lower(Document.type) == type_.lower())
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def create_document(db: AsyncSession, creator_id: int, type: Optional[str], name: str, size: int, path: str, provider: Optional[str], folder_id: Optional[int]) -> Document:
    if folder_id is not None and not await get_folder_shallow(db, folder_id):
        raise NotFoundException("Папка не найдена")
    obj = Document(type=type, name=name, size=size, path=path, provider=provider, folder_id=folder_id, creator_id=creator_id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async def update_document(db: AsyncSession, doc_id: int, type: Optional[str], name: Optional[str], size: Optional[int], path: Optional[str], provider: Optional[str], folder_id: Optional[int]) -> Document:
    doc = await get_document(db, doc_id)
    if folder_id is not None and folder_id != doc.folder_id:
        if not await get_folder_shallow(db, folder_id):
            raise NotFoundException("Папка не найдена")
        doc.folder_id = folder_id
    if type is not None:
        doc.type = type
    if name is not None:
        doc.name = name
    if size is not None:
        doc.size = size
    if path is not None:
        doc.path = path
    if provider is not None:
        doc.provider = provider
    await db.commit()
    await db.refresh(doc)
    return doc

async def delete_document(db: AsyncSession, doc_id: int) -> None:
    doc = await get_document(db, doc_id)
    await db.delete(doc)
    await db.commit()
