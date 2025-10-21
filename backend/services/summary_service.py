import json
import logging
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ValidationError

from services.rag_service import generate_structured_summary  # ✅ NEW: RAG integration
from utils.file_manager import save_structured_summary, save_summary
from utils.counter import set_progress, reset_progress, set_error

logger = logging.getLogger(__name__)

# ============================================================
# 📘 AnnualReport Data Model (JSON validation)
# ============================================================
class AnnualReport(BaseModel):
    company_name: str = Field(..., description="Name of the company as reported in the 10-K")
    cik: str = Field(..., description="Central Index Key (CIK) identifier assigned by the SEC")
    fiscal_year_end: datetime = Field(..., description="Fiscal year end date")
    filing_date: datetime = Field(..., description="Date when the 10-K was filed with the SEC")

    total_revenue: Optional[float] = None
    net_income: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    num_employees: Optional[int] = None
    auditor: Optional[str] = None

    business_description: Optional[str] = None
    risk_factors: Optional[List[str]] = None
    management_discussion: Optional[str] = None


# ============================================================
# 🧠 Main Summarization Logic (RAG-powered)
# ============================================================
async def summarize_pdf(filename: str, model: str) -> str:
    """
    Use Retrieval-Augmented Generation (RAG) to summarize a 10-K PDF.
    1. Build/reuse vector DB.
    2. Retrieve context per section.
    3. Generate structured JSON (AnnualReport schema).
    4. Save formatted PDF.
    """
    reset_progress()

    try:
        set_progress(5, "🚀 Initializing RAG-based summarization...")

        # ✅ Validate model
        valid_models = ["llama", "mistral"]
        if model not in valid_models:
            raise ValueError(f"Invalid model '{model}'. Choose from {valid_models}.")

        # 🧭 Step 1: Generate structured summary (RAG)
        set_progress(20, f"⚙️ Running {model}-based RAG summarization...")
        structured_data = generate_structured_summary(filename, model)

        # 🔍 Step 2: Validate structured JSON
        try:
            report = AnnualReport.model_validate(structured_data)
            logger.info("✅ Validated structured RAG JSON successfully.")
        except ValidationError as ve:
            logger.warning(f"⚠️ RAG JSON validation failed. Falling back. Error: {ve}")
            # fallback: save raw text summary if schema invalid
            summary_text = json.dumps(structured_data, indent=2, ensure_ascii=False)
            set_progress(85, "🪶 Saving fallback plain summary...")
            summary_path = save_summary(filename, summary_text)
            set_progress(100, "✅ Summarization complete (fallback JSON).")
            return summary_path

        # 🧾 Step 3: Render structured summary PDF
        set_progress(85, "📄 Rendering structured summary PDF...")
        summary_path = save_structured_summary(
            filename=filename,
            report=report.model_dump(),
            model_used=model,
            chunk_count=1  # chunk_count = 1 since RAG handles splitting
        )

        set_progress(100, "✅ RAG Summarization complete.")
        logger.info(f"Summary saved: {summary_path}")
        return summary_path

    except Exception as e:
        logger.error(f"❌ Summarization failed: {e}")
        set_error(str(e))
        raise RuntimeError(f"Summarization failed: {e}")
