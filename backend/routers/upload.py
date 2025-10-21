from fastapi import APIRouter, UploadFile, File, HTTPException
from utils.file_manager import save_upload

router = APIRouter()

@router.post("/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and save it in the /data/uploads folder.
    Returns the stored filename and full file path.
    """
    try:
        # Save file using file_manager
        file_path = save_upload(file)
        return {
            "success": True,
            "filename": file.filename,
            "path": file_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
