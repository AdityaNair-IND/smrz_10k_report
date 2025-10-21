from fastapi import APIRouter
from utils.counter import get_progress, reset_progress, set_progress
from services.rag_service import clear_vector_cache  # ✅ NEW: cache clearing helper

router = APIRouter()

# ============================================================
# 🚀 Progress Endpoints
# ============================================================

@router.get("/", summary="Get current summarization progress")
async def read_progress():
    """
    Returns the current progress snapshot, e.g.
    {
      "status": "summarizing",
      "progress": 42,
      "message": "Running mistral-nemo summarization..."
    }
    """
    return get_progress()


@router.post("/reset", summary="Reset progress to idle (0%)")
async def reset_progress_endpoint():
    """Reset progress to default (idle / 0%)."""
    reset_progress()
    return {"ok": True, "message": "Progress reset successfully."}


# Optional: Manual progress set for testing
@router.post("/", summary="Manually set progress (for testing)")
async def set_progress_endpoint(payload: dict):
    """
    Body:
      {
        "progress": 10,
        "status": "extracting",
        "message": "Extracting text..."
      }
    """
    value = int(payload.get("progress", 0))
    message = payload.get("message", "Manual update.")
    set_progress(value, message)
    return get_progress()

# ============================================================
# 🧹 Cache Management Endpoints
# ============================================================

@router.delete("/clear_cache", summary="Clear cached vector stores (RAM + Disk)")
async def clear_cache_endpoint():
    """
    Deletes all cached vectorstore data (Chroma persistence folders).
    Useful if embeddings are stale or you want a fresh rebuild.
    """
    deleted_dirs = clear_vector_cache()
    return {
        "ok": True,
        "message": f"Cleared {len(deleted_dirs)} cached vector directories.",
        "cleared": deleted_dirs
    }
