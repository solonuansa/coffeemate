import logging
import time
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.rag_service import RAGService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

MAX_QUESTION_LENGTH = 1000

rag_service: Optional[RAGService] = None
startup_error: Optional[str] = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=MAX_QUESTION_LENGTH)


class SourceItem(BaseModel):
    nama: str
    lokasi: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_service, startup_error

    try:
        logger.info("Initializing RAG service...")
        rag_service = RAGService()
        startup_error = None
        logger.info("RAG service initialized.")
    except Exception as exc:
        rag_service = None
        startup_error = str(exc)
        logger.exception("Failed to initialize RAG service: %s", exc)

    yield


app = FastAPI(
    title="Coffee Shop RAG API",
    description="API backend untuk sistem rekomendasi coffee shop berbasis RAG",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    status = "ok" if rag_service else "error"
    return {
        "status": status,
        "service_ready": rag_service is not None,
        "error": startup_error,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    if not rag_service:
        message = startup_error or "Service belum siap."
        raise HTTPException(status_code=503, detail=message)

    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question tidak boleh kosong.")

    started_at = time.perf_counter()
    try:
        result = rag_service.ask(question)
        latency_ms = (time.perf_counter() - started_at) * 1000
        logger.info("Chat processed in %.2f ms", latency_ms)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        latency_ms = (time.perf_counter() - started_at) * 1000
        logger.exception("Chat failed after %.2f ms: %s", latency_ms, exc)
        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan saat memproses pertanyaan.",
        ) from exc
