import os
from pathlib import Path
from dotenv import load_dotenv

# Path
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RAW_DATA_DIR = DATA_DIR / "raw"
VECTOR_STORE_DIR = DATA_DIR / "vector_store" / "chroma_db"

# Models
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"  # Sentence transformer model
GROQ_MODEL = "llama-3.3-70b-versatile"  # Groq LLM model

# Embedding
EMBEDDING_BATCH_SIZE = 32 
INGEST_BATCH_SIZE = 100  

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# API Security
API_ACCESS_TOKEN = os.getenv("API_ACCESS_TOKEN", "")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
DAILY_REQUEST_LIMIT_PER_IP = int(os.getenv("DAILY_REQUEST_LIMIT_PER_IP", "300"))
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

# Retrieval
TOP_K_RESULTS = 5 
SCORE_THRESHOLD = 0.3  

# Generation
MAX_TOKENS = 1024
TEMPERATURE = 0.7
API_TIMEOUT = 30.0 

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 2 

# System prompt
SYSTEM_PROMPT = """Anda adalah asisten yang membantu memberikan informasi coffee shop di Yogyakarta.
Berdasarkan informasi yang diberikan, berikan rekomendasi yang relevan, jelas, dan membantu.
Fokus pada lokasi, suasana, menu, dan fasilitas yang tersedia.

ATURAN FORMAT WAJIB:
1. Gunakan Markdown yang konsisten.
2. Bagian rekomendasi harus memakai bullet list, dan pada bullet HANYA tulis nama tempat.
3. Detail tiap tempat (lokasi, alasan, menu/fasilitas) tulis di baris biasa setelah bullet tempat tersebut, bukan bullet baru.
4. Jangan gunakan label internal seperti "Sumber 1", "Sumber 2", "--- Sumber ---", atau format sitasi internal sejenis.
5. Jika data tidak cukup, katakan secara jujur dan singkat.

Contoh format:
## Rekomendasi Coffee Shop
- Nama Tempat
  Lokasi: ...
  Alasan: ...
  Fasilitas/Menu: ..."""

# Prompt template 
CONTEXT_PROMPT_TEMPLATE = """Gunakan data berikut untuk menjawab pertanyaan.
Jika data tidak cukup, katakan dengan jujur.

Data:
{context}

Pertanyaan:
{query}

Jawaban:"""
