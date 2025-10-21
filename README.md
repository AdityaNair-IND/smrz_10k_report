# 🧠 SMRZ 10K Report Summarizer

A locally hosted application that summarizes **10-K annual reports** using **offline Large Language Models (LLMs)** powered by **[Ollama](https://ollama.ai)**.  
It features a minimal, responsive frontend built with React + Vite, and a FastAPI backend optimized for local inference using models like **Llama 3.1 (Meta)** and **Mistral-Nemo (Mistral AI × NVIDIA)**.

---

## 🚀 Project Overview

**SMRZ 10K Report** is designed to process complex financial reports (10-K PDFs) and produce concise, readable summaries — all locally, ensuring **data privacy** and **zero cloud dependency**.  
The backend leverages **LangChain**, **Ollama**, and a custom summarization pipeline to analyze uploaded documents efficiently using GPU acceleration.

---

## 🎥 Demo

Below is a short preview of the app in action — from file upload to downloading the summarized report:

![Demo](assets/WebsiteDemoRecording.gif)

---

## ⚙️ Backend Workflow (Simplified)

1. **File Upload**  
   The user uploads a 10-K annual report (PDF) via the web interface.  
   The backend receives the file through FastAPI, stores it temporarily, and initiates preprocessing.

2. **Preprocessing & Chunking**  
   The PDF is split into logical text chunks. Each section is tokenized and prepared for embedding.

3. **Vectorization**  
   Text chunks are embedded into vector space using locally hosted embedding models and stored in a vector database (`data/vectorstore`).

4. **Summarization Pipeline**  
   Depending on the selected model — **Llama 3.1** or **Mistral-Nemo** — the summarizer runs a multi-stage summarization process, querying relevant sections and composing concise summaries section-wise.

5. **Result Generation**  
   The summarized text is formatted and saved as a new PDF in the backend’s `/data/summaries` directory.

6. **Download**  
   Once the summarization is complete, the summarized report becomes available for download directly from the frontend — all processed locally, with no external API calls.

---

## 🧩 Key Technologies

- **Frontend:** React + Vite + TailwindCSS  
- **Backend:** FastAPI, LangChain, PyPDF, Ollama  
- **Models:** Llama 3.1 (Meta), Mistral-Nemo (Mistral AI & NVIDIA)  
- **Runtime:** Local GPU (tested on RTX 3050 4GB VRAM, 16GB RAM system)

---

## 🧠 Takeaway Notes

- During testing, it was observed that **VRAM memory bleed** occurs under sustained load — especially with 8B+ parameter models.  
- When VRAM overflows, the computation spills over into **system RAM**, which can cause:
  - Slower inference
  - Occasional inconsistent outputs (varying summary quality)
  - Process crashes due to memory exhaustion  
- Future improvements include:
  - Optimized chunking and batching
  - Better GPU memory management
  - Efficient pipeline scheduling for stable long-document summarization

---

## 🏁 Conclusion

SMRZ 10K Report demonstrates how **local LLMs** can be integrated into a practical summarization workflow without depending on cloud-based APIs — ensuring full **data privacy**, **transparency**, and **control** over computation.

---

### 🔗 Author
**Aditya Nair**  
[LinkedIn](https://www.linkedin.com/in/aditya-nair-24a096214/)