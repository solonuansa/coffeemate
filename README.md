# Coffee Shop RAG System

Sistem RAG (Retrieval-Augmented Generation) untuk rekomendasi coffee shop di Yogyakarta berbasis data Instagram, ChromaDB, dan Groq API.

## Arsitektur Saat Ini

- `frontend/`: Next.js (React + TypeScript) untuk UI chat.
- `web_api/`: FastAPI backend untuk endpoint RAG.
- `src/`: core pipeline RAG (retrieval + generation + service layer).
- `data/vector_store/chroma_db`: persistent vector store ChromaDB.

Alur request:
1. User kirim pertanyaan dari UI Next.js.
2. Next.js route `/api/chat` meneruskan request ke FastAPI (server-to-server).
3. FastAPI melakukan retrieval dari ChromaDB dan generation via Groq.
4. Jawaban + sumber dikembalikan ke UI.

## Struktur Project

```text
RAG/
  frontend/                 # Next.js app (UI chat)
    app/
      api/chat/route.ts     # Proxy route ke FastAPI
    components/
    lib/
    types/
  web_api/
    main.py                 # FastAPI entrypoint
    security.py             # In-memory guard (rate limit + daily cap)
  src/
    rag_service.py          # Orkestrasi retriever + generator
    retriever.py
    generator.py
    embed.py
    ingest.py
  config/
    settings.py             # Konfigurasi model, API, security, path
  data/
    processed/
    vector_store/chroma_db/
  app.py                    # CLI mode
  reingest.py               # Rebuild vector store
  requirements.txt
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- npm 10+

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Frontend dependencies

```bash
cd frontend
npm install
```

### 3. Konfigurasi environment backend (`.env` di root)

Contoh:

```env
GROQ_API_KEY=your_groq_api_key

# Optional security hardening
API_ACCESS_TOKEN=your_strong_token
RATE_LIMIT_PER_MINUTE=20
DAILY_REQUEST_LIMIT_PER_IP=300
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 4. Konfigurasi environment frontend (`frontend/.env.local`)

Bisa salin dari `frontend/.env.local.example`.

```env
BACKEND_API_URL=http://127.0.0.1:8000/api/chat
BACKEND_API_TOKEN=your_strong_token
```

`BACKEND_API_TOKEN` harus sama dengan `API_ACCESS_TOKEN` jika backend token protection diaktifkan.

## Menjalankan Aplikasi (Web)

Jalankan backend FastAPI:

```bash
uvicorn web_api.main:app --reload
```

Jalankan frontend Next.js (terminal terpisah):

```bash
cd frontend
npm run dev
```

Lalu buka: `http://localhost:3000`

## Menjalankan Aplikasi (CLI)

```bash
python app.py
```

## API Endpoints

### `GET /health`

Status kesiapan service backend.

Contoh response:

```json
{
  "status": "ok",
  "service_ready": true,
  "error": null
}
```

### `POST /api/chat`

Request:

```json
{
  "question": "Rekomendasikan coffee shop untuk WFC di Sleman"
}
```

Response:

```json
{
  "answer": "Rekomendasi ...",
  "sources": [
    { "nama": "Nama Coffee Shop", "lokasi": "Sleman" }
  ]
}
```

## Security dan Usage Guard

Backend saat ini sudah memiliki:
- Optional bearer token auth (`API_ACCESS_TOKEN`).
- Rate limit per IP (`RATE_LIMIT_PER_MINUTE`).
- Daily cap per IP (`DAILY_REQUEST_LIMIT_PER_IP`).
- Security headers (`X-Frame-Options`, `X-Content-Type-Options`, dll).
- CORS origin whitelist (`ALLOWED_ORIGINS`).

Catatan:
- Guard saat ini berbasis in-memory (`web_api/security.py`) dan cocok untuk single instance.
- Untuk multi-instance production, ganti ke shared store (misalnya Redis).

## Rebuild Vector Store

Jika data processed berubah:

```bash
python reingest.py
```

## Deployment Rekomendasi

- Frontend: Vercel.
- Backend FastAPI: Render / Railway / Fly.io (non-serverless lebih aman untuk workload RAG + storage).
- Simpan `GROQ_API_KEY` dan token security via environment variables platform deploy.
- Gunakan persistent volume jika tetap memakai ChromaDB lokal.

## Catatan Tambahan

- Model embedding akan diunduh saat first run jika belum ada cache.
- Folder `data/vector_store/` dan `.env` sebaiknya tidak di-track git.
- Terdapat deprecation warning untuk class Chroma dari LangChain; ke depan disarankan migrasi ke `langchain-chroma`.
