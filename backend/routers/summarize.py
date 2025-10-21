from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.summary_service import summarize_pdf

router = APIRouter()

class SummarizeRequest(BaseModel):
    filename: str
    model: str  # "llama" or "mistral"

@router.post("/")
async def summarize_file(request: SummarizeRequest):
    """
    Summarize the uploaded PDF using the user-selected model.
    """
    try:
        summary_path = await summarize_pdf(request.filename, request.model)
        return {"summary_path": summary_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
