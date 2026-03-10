import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Path
BASE_DIR = Path(__file__).parent.parent
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
Jika informasi tidak cukup, katakan dengan jujur."""

# Prompt template 
CONTEXT_PROMPT_TEMPLATE = """Gunakan data berikut untuk menjawab pertanyaan.
Jika data tidak cukup, katakan dengan jujur.

Data:
{context}

Pertanyaan:
{query}

Jawaban:"""
