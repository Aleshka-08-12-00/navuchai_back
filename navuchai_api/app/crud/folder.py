from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.folder import Folder
from app.models.document import Document
from app.exceptions import NotFoundException, DatabaseException

async def get_folder(db: AsyncSession, folder_id: int) -> Folder:
    result = await db.execute(
        select(Folder)
        .options(selectinload(Folder.children))
        .options(selectinload(Folder.documents))
        .where(Folder.id == folder_id)
    )
    folder = result.scalar_one_or_none()
    if not folder:
        raise NotFoundException("Папка не найдена")
    return folder

async def get_folder_shallow(db: AsyncSession, folder_id: int) -> Folder | None:
    result = await db.execute(select(Folder).where(Folder.id == folder_id))
    return result.scalar_one_or_none()

async def list_folders(db: AsyncSession, parent_id: Optional[int], q: Optional[str], skip: int, limit: int) -> List[Folder]:
    stmt = select(Folder).options(selectinload(Folder.children)).order_by(Folder.id)
    if parent_id is None:
        stmt = stmt.where(Folder.parent_id.is_(None))
    else:
        stmt = stmt.where(Folder.parent_id == parent_id)
    if q:
        stmt = stmt.where(func.lower(Folder.name).like(f"%{q.lower()}%"))
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def create_folder(db: AsyncSession, name: str, creator_id: int, parent_id: Optional[int]) -> Folder:
    if parent_id is not None and not await get_folder_shallow(db, parent_id):
        raise NotFoundException("Родительская папка не найдена")
    obj = Folder(name=name, parent_id=parent_id, creator_id=creator_id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async def update_folder(db: AsyncSession, folder_id: int, name: Optional[str], parent_id: Optional[int]) -> Folder:
    folder = await get_folder(db, folder_id)
    if parent_id == folder_id:
        raise DatabaseException("Папка не может быть своим родителем")
    if parent_id is not None and parent_id != folder.parent_id:
        if not await get_folder_shallow(db, parent_id):
            raise NotFoundException("Родительская папка не найдена")
        folder.parent_id = parent_id
    if name is not None:
        folder.name = name
    await db.commit()
    await db.refresh(folder)
    return folder

async def delete_folder(db: AsyncSession, folder_id: int) -> None:
    folder = await get_folder(db, folder_id)
    await db.delete(folder)
    await db.commit()

async def list_folder_content(db: AsyncSession, folder_id: int, q: Optional[str], type_: Optional[str], skip: int, limit: int) -> Tuple[List[Folder], List[Document]]:
    await get_folder(db, folder_id)
    f_stmt = select(Folder).where(Folder.parent_id == folder_id).order_by(Folder.id).offset(skip).limit(limit)
    if q:
        f_stmt = f_stmt.where(func.lower(Folder.name).like(f"%{q.lower()}%"))
    d_stmt = select(Document).where(Document.folder_id == folder_id).order_by(Document.id).offset(skip).limit(limit)
    if q:
        d_stmt = d_stmt.where(func.lower(Document.name).like(f"%{q.lower()}%"))
    if type_:
        d_stmt = d_stmt.where(func.lower(Document.type) == type_.lower())
    f_res = await db.execute(f_stmt)
    d_res = await db.execute(d_stmt)
    return f_res.scalars().all(), d_res.scalars().all()
