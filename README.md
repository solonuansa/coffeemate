# CoffeeMate RAG System

Sistem tanya-jawab dan rekomendasi coffee shop berbasis RAG (Retrieval-Augmented Generation) untuk wilayah Yogyakarta. Proyek ini menggabungkan pencarian dokumen terstruktur dari data Instagram dengan generasi jawaban menggunakan LLM. Tujuannya memberikan rekomendasi tempat ngopi yang sesuai dengan preferensi pengguna, berdasarkan data aktual dari media sosial. Data yang digunakan berasal dari scraping akun Instagram [@referensikopi](https://www.instagram.com/referensikopi/).

## Live Demo

- Production Web UI: https://mycoffeemate.vercel.app/

## Web UI Preview

![Home](docs/assets/web-ui/rag-coffeeshop.png)

## Apa yang Diselesaikan Proyek Ini

Pengguna dapat bertanya seperti:
- "Rekomendasi coffee shop untuk WFC di Sleman"
- "Tempat dengan suasana tenang dan menu kopi susu"

Lalu sistem akan:
1. Mengambil dokumen paling relevan dari vector store.
2. Menyusun konteks dari metadata dan deskripsi tempat.
3. Menghasilkan jawaban terformat dengan sumber asal data.

## Fitur Utama

- Pipeline RAG end-to-end: retrieval + generation.
- API backend FastAPI siap dipakai frontend.
- Web UI berbasis Next.js dengan server-side proxy ke backend (`/api/chat`).
- Mode CLI untuk query langsung tanpa UI.
- Auto-rebuild vector store saat startup jika storage kosong/tidak persisten.
- Proteksi API:
  - bearer token opsional,
  - rate limit per menit per IP,
  - daily cap per IP (`DAILY_REQUEST_LIMIT_PER_IP`),
  - CORS allowlist,
  - security headers pada response.

## Arsitektur Singkat

1. Browser mengirim request ke route Next.js `frontend/app/api/chat/route.ts`.
2. Route tersebut meneruskan request ke FastAPI (`backend/web_api/main.py`).
3. FastAPI menjalankan validasi token + usage guard.
4. `RAGService` mengorkestrasi `Retriever` + `Generator`.
5. Jawaban dan daftar sumber dikembalikan ke frontend.

## Stack Teknologi

- Backend: FastAPI, Pydantic, LangChain, ChromaDB.
- Retrieval/Embedding: model Jina (`jina-embeddings-v5-text-small`), data vector di Chroma.
- Generation: Groq API (`llama-3.3-70b-versatile`).
- Frontend: Next.js (App Router, route handler sebagai proxy backend).
- Data processing: pandas untuk ingest CSV menjadi dokumen.

## Struktur Direktori Inti

```text
backend/
  config/settings.py
  src/
    rag_service.py
    retriever.py
    generator.py
    ingest.py
    embed.py
  web_api/
    main.py
    security.py
frontend/
  app/api/chat/route.ts
scripts/
  cli.py
  reingest.py
docs/
  CODE_DOCUMENTATION.md
  WEB_UI_DEPLOYMENT_PLAN.md
```

## Konfigurasi Penting

Di `.env` root:
- `GROQ_API_KEY`: wajib untuk generation.
- `JINA_API_KEY`: wajib untuk embedding Jina.
- `API_ACCESS_TOKEN`: opsional, aktifkan auth bearer jika diisi.
- `RATE_LIMIT_PER_MINUTE`: batas request per menit per IP.
- `DAILY_REQUEST_LIMIT_PER_IP`: batas request harian per IP.
- `ALLOWED_ORIGINS`: daftar origin frontend yang diizinkan CORS.

Di `frontend/.env.local`:
- `BACKEND_API_URL`: URL endpoint backend `/api/chat`.
- `BACKEND_API_TOKEN`: token backend (samakan dengan `API_ACCESS_TOKEN` jika auth diaktifkan).

## API Kontrak

- `GET /health`: status kesiapan service.
- `POST /api/chat`: proses pertanyaan RAG.

Request:
```json
{
  "question": "Rekomendasikan coffee shop untuk WFC di Sleman"
}
```

Response:
```json
{
  "answer": "....",
  "sources": [
    { "nama": "@akun_ig", "lokasi": "Sleman" }
  ]
}
```

## Setup Singkat

```bash
pip install -r requirements.txt
cd frontend && npm install
```

Buat `.env` di root dan `frontend/.env.local`, lalu jalankan:

```bash
uvicorn backend.web_api.main:app --reload
cd frontend && npm run dev:3010
```

Mode CLI:

```bash
python scripts/cli.py
```

Rebuild vector store:

```bash
python scripts/reingest.py
```
