from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from utils.file_manager import get_summary_file

router = APIRouter()

@router.get("/{filename}")
async def download_summary(filename: str):
    """
    Download summarized report (Markdown or PDF) from /data/summaries folder.
    """
    try:
        file_path = get_summary_file(filename)
        media_type = "application/pdf" if filename.endswith(".pdf") else "text/markdown"
        return FileResponse(path=file_path, media_type=media_type, filename=filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Summary file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {e}")
