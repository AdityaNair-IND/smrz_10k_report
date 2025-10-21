import fitz  # PyMuPDF

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts plain text from all pages of a PDF file using PyMuPDF.
    Ensures resources are cleaned up and output is trimmed.
    """
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                page_text = page.get_text("text")
                if page_text:
                    text += page_text.strip() + "\n\n"
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {e}")

    cleaned_text = text.strip()
    if not cleaned_text:
        raise ValueError("No text content found in the provided PDF.")
    return cleaned_text
