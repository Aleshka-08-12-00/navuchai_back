from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.crud import authorized_required, get_current_user, root_admin_moderator_required
from app.schemas.folder import FolderCreate, FolderUpdate, FolderResponse
from app.schemas.file_manager import FolderContentResponse
from app.crud.folder import list_folders, get_folder, create_folder, update_folder, delete_folder, list_folder_content
from app.exceptions import NotFoundException
from app.models import User

router = APIRouter(prefix="/api/folders", tags=["Folders"])

@router.get("/", response_model=list[FolderResponse], dependencies=[Depends(authorized_required)])
async def list_route(db: AsyncSession = Depends(get_db), parent_id: Optional[int] = Query(default=None, alias="parentId"), q: Optional[str] = None, skip: int = 0, limit: int = Query(50, le=200)):
    return await list_folders(db, parent_id, q, skip, limit)

@router.get("/{folder_id}/", response_model=FolderResponse, dependencies=[Depends(authorized_required)])
async def read_route(folder_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await get_folder(db, folder_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/", response_model=FolderResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(root_admin_moderator_required)])
async def create_route(data: FolderCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await create_folder(db, data.name, user.id, data.parent_id)

@router.put("/{folder_id}/", response_model=FolderResponse, dependencies=[Depends(root_admin_moderator_required)])
async def update_route(folder_id: int, data: FolderUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await update_folder(db, folder_id, data.name, data.parent_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{folder_id}/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(root_admin_moderator_required)])
async def delete_route(folder_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await delete_folder(db, folder_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{folder_id}/content/", response_model=FolderContentResponse, dependencies=[Depends(authorized_required)])
async def content_route(folder_id: int, db: AsyncSession = Depends(get_db), q: Optional[str] = None, type: Optional[str] = None, skip: int = 0, limit: int = Query(50, le=200)):
    try:
        folders, documents = await list_folder_content(db, folder_id, q, type, skip, limit)
        return {"folders": folders, "documents": documents}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
