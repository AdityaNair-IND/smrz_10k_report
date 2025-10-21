import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple

from services.pdf_service import extract_text_from_pdf
from services.ollama_service import run_ollama
from utils.counter import set_progress

# LangChain components (modern imports)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

logger = logging.getLogger(__name__)

# === Persistent Vectorstore Root ===
VECTOR_ROOT = Path("data/vectorstore")
VECTOR_ROOT.mkdir(parents=True, exist_ok=True)

# === Default Embedding Model ===
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# === Model Mapping ===
MODEL_MAP = {
    "llama": "llama3.1:8b",
    "mistral": "mistral-nemo:12b",
}

# === Runtime Cache (RAM) ===
_SESSION_CACHE: Dict[str, Dict] = {
    # "pdf_stem": {"vectordb": Chroma, "chunks": int}
}


def _model_name(model_choice: str) -> str:
    if model_choice not in MODEL_MAP:
        raise ValueError(f"Invalid model '{model_choice}'. Must be one of {list(MODEL_MAP.keys())}")
    return MODEL_MAP[model_choice]


def _split_text(text: str, chunk_size: int = 1200, chunk_overlap: int = 150) -> List[str]:
    """
    Split text into overlapping chunks for embedding.
    Tuned for ~4GB VRAM GPUs (RTX 3050 sweet spot).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


# ============================================================
# 🧠 Cached Vectorstore Builder
# ============================================================
def _ensure_vectorstore(pdf_path: str) -> Tuple[Chroma, int]:
    """
    Build or reuse a Chroma vectorstore (RAM + disk cached).
    Returns (vectorstore, num_docs).
    """
    set_progress(18, "🔍 Preparing vector index...")

    stem = Path(pdf_path).stem
    persist_dir = VECTOR_ROOT / stem
    persist_dir.mkdir(parents=True, exist_ok=True)

    # ✅ Check RAM cache first
    if stem in _SESSION_CACHE:
        logger.info(f"⚡ Using in-memory cached vectorstore for '{stem}'")
        cached = _SESSION_CACHE[stem]
        return cached["vectordb"], cached["chunks"]

    # ✅ Check disk persistence next
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    try:
        vectordb = Chroma(
            collection_name=f"10k_{stem}",
            embedding_function=embeddings,
            persist_directory=str(persist_dir),
        )
        count = vectordb._collection.count()
        if count > 0:
            logger.info(f"💾 Loaded persisted vectorstore for '{stem}' with {count} chunks")
            _SESSION_CACHE[stem] = {"vectordb": vectordb, "chunks": count}
            return vectordb, count
    except Exception as e:
        logger.warning(f"⚠️ Could not load persisted vectorstore, rebuilding: {e}")

    # ✅ Rebuild embeddings if no cache found
    set_progress(25, "📖 Reading and embedding document...")
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text.strip():
        raise ValueError("No text extracted from PDF.")

    chunks = _split_text(raw_text)
    if not chunks:
        raise ValueError("Failed to split text into chunks.")

    vectordb = Chroma(
        collection_name=f"10k_{stem}",
        embedding_function=embeddings,
        persist_directory=str(persist_dir),
    )
    vectordb.add_texts(chunks)
    vectordb.persist()

    logger.info(f"✅ Built new vectorstore for '{stem}' with {len(chunks)} chunks.")
    _SESSION_CACHE[stem] = {"vectordb": vectordb, "chunks": len(chunks)}

    return vectordb, len(chunks)


# ============================================================
# 🎯 Retrieval + LLM Helpers
# ============================================================
def _retrieve(vectordb: Chroma, query: str, k: int = 6) -> str:
    """Retrieve top-k passages and join them as context."""
    docs = vectordb.similarity_search(query, k=k)
    return "\n\n".join(d.page_content for d in docs)


def _ask_llm(model_name: str, system_instructions: str, context: str, question: str, force_json: bool = False) -> str:
    """Ask the LLM a targeted question with RAG context."""
    if force_json:
        prompt = (
            f"{system_instructions}\n\n"
            f"Context:\n---\n{context}\n---\n\n"
            f"{question}\n\n"
            f"Return ONLY valid JSON. No markdown, no commentary."
        )
    else:
        prompt = (
            f"{system_instructions}\n\n"
            f"Context:\n---\n{context}\n---\n\n"
            f"{question}"
        )
    return run_ollama(model_name, prompt)


def _safe_json_extract(s: str) -> str:
    """Extract JSON safely from model response."""
    start, end = s.find("{"), s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return s[start : end + 1]
    return s.strip()


# ============================================================
# 🧩 Main Structured Summary Generator
# ============================================================
def generate_structured_summary(pdf_filename: str, model_choice: str) -> Dict:
    """
    Full section-wise RAG pipeline with caching & persistence.
    """
    model_name = _model_name(model_choice)
    pdf_path = f"data/uploads/{pdf_filename}"

    set_progress(15, "⚙️ Initializing RAG pipeline...")
    vectordb, vec_count = _ensure_vectorstore(pdf_path)

    # Section queries
    set_progress(35, "🔎 Retrieving relevant sections...")
    queries = {
        "company_meta": "Extract the company name, CIK, fiscal year end, and filing date from the cover or intro.",
        "financials": "Summarize revenue, net income, assets, liabilities, cash flow, and cash equivalents.",
        "business_description": "Summarize the business overview (segments, markets, main products).",
        "risk_factors": "List top risk factors (Item 1A) as 5–10 concise bullets.",
        "mda": "Summarize MD&A (Item 7): performance drivers, key risks, outlook.",
        "employees_auditor": "Extract number of employees and external auditor if present.",
    }

    # Retrieve context
    ctx = {key: _retrieve(vectordb, q, k=6) for key, q in queries.items()}

    set_progress(55, f"💬 Querying {model_name} for section insights...")
    sys = "You are a precise SEC analyst. Use only the provided context. Be factual."

    answers = {}
    for key, question in queries.items():
        answers[key] = _ask_llm(model_name, sys, ctx[key], question, force_json=False)

    # Assemble final structured JSON
    set_progress(75, "🧱 Building structured AnnualReport JSON...")
    schema = {
        "company_name": "string",
        "cik": "string",
        "fiscal_year_end": "YYYY-MM-DD",
        "filing_date": "YYYY-MM-DD",
        "total_revenue": "number or null",
        "net_income": "number or null",
        "total_assets": "number or null",
        "total_liabilities": "number or null",
        "operating_cash_flow": "number or null",
        "cash_and_equivalents": "number or null",
        "num_employees": "integer or null",
        "auditor": "string or null",
        "business_description": "string or null",
        "risk_factors": "list of strings or null",
        "management_discussion": "string or null",
    }

    final_context = "\n\n".join(f"[{k.upper()}]\n{v}" for k, v in answers.items())
    final_prompt = (
        "Using ONLY the provided Context, assemble a valid JSON for the AnnualReport schema.\n"
        f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
        "Rules:\n- Use null if unknown\n- Dates = YYYY-MM-DD\n- risk_factors = array of strings\n"
        "- No markdown, no commentary. Output JSON only."
    )

    set_progress(85, f"🧠 Generating final structured JSON via {model_name}...")
    final_raw = _ask_llm(model_name, sys, final_context, final_prompt, force_json=True)
    final_json = _safe_json_extract(final_raw)

    try:
        data = json.loads(final_json)
        logger.info("✅ Structured JSON assembled successfully.")
        return data
    except Exception as e:
        logger.warning(f"⚠️ JSON parse failed, returning raw fallback. {e}")
        return {"_raw_text": final_raw}

# ============================================================
# 🧹 Cache Clearing Utility
# ============================================================
def clear_vector_cache() -> List[str]:
    """
    Clears all cached vector stores from both memory (_SESSION_CACHE)
    and disk (data/vectorstore/*).
    Returns list of deleted directory names.
    """
    deleted_dirs = []

    # 1️⃣ Clear in-memory cache
    _SESSION_CACHE.clear()
    logger.info("🧠 In-memory vector cache cleared.")

    # 2️⃣ Remove persistent Chroma folders
    if VECTOR_ROOT.exists():
        for child in VECTOR_ROOT.iterdir():
            if child.is_dir():
                try:
                    for sub in child.rglob("*"):
                        if sub.is_file():
                            sub.unlink()
                    for sub in sorted(child.rglob("*"), reverse=True):
                        if sub.is_dir():
                            sub.rmdir()
                    child.rmdir()
                    deleted_dirs.append(child.name)
                    logger.info(f"🧹 Deleted vectorstore folder: {child.name}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to delete {child.name}: {e}")

    return deleted_dirs
