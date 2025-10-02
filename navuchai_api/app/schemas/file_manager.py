from typing import List
from pydantic import BaseModel
from app.schemas.folder import FolderResponse
from app.schemas.document import DocumentResponse

class FolderContentResponse(BaseModel):
    folders: List[FolderResponse]
    documents: List[DocumentResponse]
