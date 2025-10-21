from typing import Dict
from threading import Lock

# === Global state ===
_progress_state: Dict[str, any] = {
    "status": "idle",         # idle | running | completed | error
    "progress": 0,            # integer 0–100
    "message": "Waiting for summarization."
}

_lock = Lock()


# ============================================================
# 🧭 Core Progress Functions
# ============================================================
def set_progress(value: int, message: str = ""):
    """Set absolute progress (0–100) with optional message."""
    with _lock:
        _progress_state["progress"] = max(0, min(value, 100))
        if message:
            _progress_state["message"] = message
        if value >= 100:
            _progress_state["status"] = "completed"
        elif value > 0:
            _progress_state["status"] = "running"


def reset_progress():
    """Reset to idle state."""
    with _lock:
        _progress_state.update({
            "status": "idle",
            "progress": 0,
            "message": "Waiting for summarization."
        })


def set_error(message: str):
    """Mark progress as errored."""
    with _lock:
        _progress_state.update({
            "status": "error",
            "progress": 100,
            "message": f"❌ {message}"
        })


def get_progress() -> Dict[str, any]:
    """Return a snapshot of current progress state."""
    with _lock:
        return _progress_state.copy()


# ============================================================
# 🔁 Chunk-based Incremental Progress
# ============================================================
def set_chunk_progress(current_chunk: int, total_chunks: int, phase: str = "Summarizing"):
    """
    Smoothly updates overall progress based on current chunk count.
    Example: current_chunk=2, total_chunks=5 → progress ≈ 40%.
    """
    if total_chunks <= 0:
        return

    base_start = 20   # after extraction
    base_end = 85     # before rendering
    chunk_range = base_end - base_start
    progress_per_chunk = chunk_range / total_chunks

    progress_value = int(base_start + (current_chunk * progress_per_chunk))
    message = f"{phase} chunk {current_chunk}/{total_chunks}..."

    set_progress(progress_value, message)
