import logging
import time
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config.settings import (
    ALLOWED_ORIGINS,
    API_ACCESS_TOKEN,
    DAILY_REQUEST_LIMIT_PER_IP,
    RATE_LIMIT_PER_MINUTE,
)
from src.rag_service import RAGService
from web_api.security import InMemoryUsageGuard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

MAX_QUESTION_LENGTH = 500

rag_service: Optional[RAGService] = None
startup_error: Optional[str] = None
usage_guard = InMemoryUsageGuard(
    per_minute_limit=RATE_LIMIT_PER_MINUTE,
    daily_limit_per_ip=DAILY_REQUEST_LIMIT_PER_IP,
)


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
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def enforce_access_token(request: Request) -> None:
    if not API_ACCESS_TOKEN:
        return

    auth_header = request.headers.get("authorization", "")
    expected = f"Bearer {API_ACCESS_TOKEN}"
    if auth_header != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized.",
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
def chat(payload: ChatRequest, request: Request):
    if not rag_service:
        message = startup_error or "Service belum siap."
        raise HTTPException(status_code=503, detail=message)

    enforce_access_token(request)

    client_ip = get_client_ip(request)
    limit_result = usage_guard.check_and_consume(client_ip)
    if not limit_result.allowed:
        raise HTTPException(
            status_code=429,
            detail=limit_result.detail,
            headers={"Retry-After": str(limit_result.retry_after_seconds)},
        )

    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question tidak boleh kosong.")

    started_at = time.perf_counter()
    try:
        result = rag_service.ask(question)
        latency_ms = (time.perf_counter() - started_at) * 1000
        logger.info("Chat processed in %.2f ms (ip=%s)", latency_ms, client_ip)
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
