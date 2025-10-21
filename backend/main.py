from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, download, summarize, progress
import os
import logging

# 🧠 Import Ollama session cleanup
from services.ollama_service import close_all_sessions

# === Logging Setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === App Initialization ===
app = FastAPI(
    title="SMRZ 10K Report Summarizer",
    version="1.0",
    description="Backend API for summarizing 10-K annual reports using local LLMs (Llama 3.1 & Mistral-Nemo)."
)

# === CORS Setup (Frontend → Backend Communication) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ for dev; replace with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Directory Setup on Startup ===
@app.on_event("startup")
async def create_data_folders():
    folders = ["data", "data/uploads", "data/summaries", "data/vectorstore"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"📁 Created folder: {folder}")

    logger.info("🚀 SMRZ 10K Summarizer Backend started successfully.")


# === Graceful Shutdown (Close LLM Sessions) ===
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🧹 Shutting down... closing Ollama sessions.")
    try:
        close_all_sessions()
        logger.info("✅ All Ollama sessions closed successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Failed to close Ollama sessions cleanly: {e}")


# === Routers ===
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(summarize.router, prefix="/summarize", tags=["Summarize"])
app.include_router(download.router, prefix="/download", tags=["Download"])
app.include_router(progress.router, prefix="/progress", tags=["Progress"])

# === Root Endpoint ===
@app.get("/")
async def root():
    return {
        "message": "Welcome to SMRZ 10K Report Summarizer Backend 🚀",
        "routes": ["/upload", "/summarize", "/download", "/progress"]
    }
