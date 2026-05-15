import mimetypes

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.services.file_storage_service import get_storage

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/{key:path}")
def get_file(key: str):
    try:
        data = get_storage().read(key)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    media_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
    return Response(content=data, media_type=media_type)
