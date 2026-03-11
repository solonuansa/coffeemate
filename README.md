# Coffee Shop RAG System

Sistem RAG (Retrieval-Augmented Generation) untuk rekomendasi coffee shop di Yogyakarta berbasis data Instagram, ChromaDB, dan Groq API.

## Struktur Proyek

```text
RAG/
  backend/
    config/
      settings.py
    src/
      rag_service.py
      retriever.py
      generator.py
      embed.py
      ingest.py
    web_api/
      main.py
      security.py
  frontend/
    app/
      api/chat/route.ts
    components/
    lib/
    types/
  scripts/
    cli.py
    reingest.py
  docs/
    CODE_DOCUMENTATION.md
    WEB_UI_DEPLOYMENT_PLAN.md
  experiments/
  data/
    processed/
    vector_store/chroma_db/
  requirements.txt
```

## Prasyarat

- Python 3.11+
- Node.js 20+
- npm 10+

## Setup

1. Install dependency backend:

```bash
pip install -r requirements.txt
```

2. Install dependency frontend:

```bash
cd frontend
npm install
```

3. Buat `.env` di root proyek:

```env
GROQ_API_KEY=your_groq_api_key

# Optional security hardening
API_ACCESS_TOKEN=your_strong_token
RATE_LIMIT_PER_MINUTE=20
DAILY_REQUEST_LIMIT_PER_IP=300
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

4. Buat `frontend/.env.local` (bisa copy dari `frontend/.env.local.example`):

```env
BACKEND_API_URL=http://127.0.0.1:8000/api/chat
BACKEND_API_TOKEN=your_strong_token
```

Catatan: jika `API_ACCESS_TOKEN` di backend diisi, `BACKEND_API_TOKEN` harus sama.

## Menjalankan Aplikasi Web

1. Jalankan backend FastAPI dari root:

```bash
uvicorn backend.web_api.main:app --reload
```

2. Jalankan frontend (terminal lain):

```bash
cd frontend
npm run dev:3010
```

3. Buka `http://localhost:3010`.

## Menjalankan Mode CLI

```bash
python scripts/cli.py
```

## Rebuild Vector Store

Jika data di `data/processed` berubah:

```bash
python scripts/reingest.py
```

## API Endpoint

- `GET /health` untuk status service.
- `POST /api/chat` untuk query RAG.

Contoh payload:

```json
{
  "question": "Rekomendasikan coffee shop untuk WFC di Sleman"
}
```

## Security Saat Ini

- Optional bearer token (`API_ACCESS_TOKEN`).
- Rate limit per IP (`RATE_LIMIT_PER_MINUTE`).
- Daily cap per IP (`DAILY_REQUEST_LIMIT_PER_IP`).
- CORS whitelist (`ALLOWED_ORIGINS`).
- Security headers di middleware FastAPI.

Catatan: limiter masih in-memory (`backend/web_api/security.py`), cocok untuk single instance.

## Deployment Ringkas

- Frontend: Vercel.
- Backend: Render / Railway / Fly.io.
- Gunakan persistent volume jika tetap menyimpan ChromaDB secara lokal.
- Untuk Railway tanpa persistent volume, backend akan auto-build vector store saat startup dari `data/processed/extracted_data_sahabatai.csv`.
- Pastikan `JINA_API_KEY` tersedia di environment Railway agar proses auto-build berhasil.
