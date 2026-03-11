# Web UI and Deployment Plan - Next.js + FastAPI

## 1. Tujuan
- Menjalankan UI chat production-ready di Vercel.
- Menjaga backend RAG tetap stabil di service terpisah (FastAPI).
- Menjaga keamanan API key dan kontrol usage.

## 2. Arsitektur Deploy (Current)
- Frontend: `Next.js` di Vercel.
- Frontend route server-side: `frontend/app/api/chat/route.ts` (proxy ke backend).
- Backend: `FastAPI` (`web_api/main.py`) di Render/Railway/Fly (recommended non-serverless).
- Vector store: `ChromaDB` persisted volume di backend platform.

Flow:
1. Browser hit `POST /api/chat` (Vercel).
2. Vercel function forward ke FastAPI (`BACKEND_API_URL`).
3. FastAPI validate auth token + rate-limit + daily cap.
4. FastAPI panggil RAG pipeline -> return answer+sumber.

## 3. Status Implementasi
- [x] Phase 1: FastAPI API layer + service abstraction (`src/rag_service.py`)
- [x] Phase 2: Next.js app setup + chat UI + API proxy route
- [x] Security baseline:
  - optional bearer token (`API_ACCESS_TOKEN`)
  - per-IP rate-limit (`RATE_LIMIT_PER_MINUTE`)
  - daily cap per-IP (`DAILY_REQUEST_LIMIT_PER_IP`)
  - CORS whitelist (`ALLOWED_ORIGINS`)
  - security headers di backend

## 4. Environment Variables

### Backend (`.env` di backend service)
- `GROQ_API_KEY=...`
- `API_ACCESS_TOKEN=...` (recommended)
- `RATE_LIMIT_PER_MINUTE=20`
- `DAILY_REQUEST_LIMIT_PER_IP=300`
- `ALLOWED_ORIGINS=https://<your-vercel-domain>,http://localhost:3000,http://127.0.0.1:3000`

### Frontend Vercel (Project Settings > Environment Variables)
- `BACKEND_API_URL=https://<your-backend-domain>/api/chat`
- `BACKEND_API_TOKEN=<same value as API_ACCESS_TOKEN backend>`

Catatan:
- Tidak perlu `NEXT_PUBLIC_API_BASE_URL` untuk arsitektur ini.
- `BACKEND_API_TOKEN` aman karena dipakai server-side di route handler Next.js.

## 5. Step-by-Step Deployment (Recommended)

### A. Deploy Backend FastAPI dulu
1. Push repo ke GitHub.
2. Buat service backend di Render/Railway/Fly.
3. Set build/start command:
   - build: `pip install -r requirements.txt`
   - start: `uvicorn web_api.main:app --host 0.0.0.0 --port $PORT`
4. Mount persistent volume untuk `data/vector_store/chroma_db`.
5. Set semua env backend (lihat section 4).
6. Verify:
   - `GET /health` -> `service_ready: true`
   - `POST /api/chat` -> 200 (dengan Authorization jika token aktif)

### B. Deploy Frontend ke Vercel
1. Import project dari GitHub ke Vercel.
2. Root directory: `frontend`.
3. Framework: Next.js (auto-detected).
4. Tambahkan env Vercel:
   - `BACKEND_API_URL`
   - `BACKEND_API_TOKEN`
5. Deploy.

### C. Integrasi CORS dan Domain
1. Ambil domain Vercel final (mis. `https://coffeemate.vercel.app`).
2. Tambahkan domain tersebut ke `ALLOWED_ORIGINS` backend.
3. Redeploy backend agar CORS baru aktif.

## 6. Verifikasi Pasca Deploy
- [ ] UI kebuka normal dari domain Vercel.
- [ ] Query berhasil (network browser hit `POST /api/chat` Vercel, bukan backend langsung).
- [ ] Backend menerima request valid dan return answer+sumber.
- [ ] Token invalid -> backend return 401.
- [ ] Burst request -> backend return 429 sesuai rate-limit.
- [ ] Tidak ada credential atau token tampil di browser DevTools (client env).

## 7. Monitoring dan Operasional
- Log wajib:
  - latency request,
  - status code,
  - 401 dan 429 frequency,
  - error 5xx.
- Alert minimum:
  - spike 5xx,
  - spike latency,
  - usage limit harian hampir habis.
- Rotasi token:
  - ubah `API_ACCESS_TOKEN` backend,
  - update `BACKEND_API_TOKEN` di Vercel,
  - redeploy keduanya.

## 8. Security Hardening (Next)
- Tambahkan WAF/rate limiting edge (Cloudflare/Vercel Firewall) di depan frontend.
- Tambahkan logging usage per session/user-id (jika auth user sudah ada).
- Pindahkan in-memory limiter ke Redis untuk multi-instance backend.

## 9. Risiko dan Mitigasi
- Risiko: backend cold start / model load lambat.
  - Mitigasi: gunakan service non-sleep, warm instance.
- Risiko: limiter in-memory tidak sinkron antar instance.
  - Mitigasi: migrasi limiter ke Redis.
- Risiko: Chroma persistence di volume lokal service.
  - Mitigasi: backup berkala atau rencana migrasi ke pgvector.

## 10. Keputusan Platform
- Vercel tepat untuk UI Next.js.
- Vercel tidak disarankan untuk full backend RAG Python + local Chroma persistence.
- Kombinasi yang dipakai:
  - Frontend: Vercel
  - Backend: Render/Railway/Fly (recommended)
