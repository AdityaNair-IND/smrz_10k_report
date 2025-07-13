import os
import fitz
from google import genai
from dotenv import load_dotenv
from google.genai.types import HttpOptions


load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"), http_options=HttpOptions(api_version="v1"))


def extract_text_from_pdf(path: str) -> str:
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)


def count_tokens(text: str, model: str = "gemini-2.5-flash") -> int:
    response = client.models.count_tokens(model=model, contents=text)
    return response.total_tokens


# === for standalone testing ===
if __name__ == "__main__":
    path = r"company_10k_report.pdf"
    text = extract_text_from_pdf(path)
    tokens = count_tokens(text)
    print(f"\n\nToken count for {path}: {tokens}")
