# Web UI Deployment Plan - Next.js + FastAPI

## 1. Target Deployment

- Frontend production aktif di Vercel.
- Backend RAG berjalan terpisah (non-serverless) agar startup model/vector store lebih stabil.
- Jalur request aman: browser tidak berkomunikasi langsung ke backend, tetapi lewat route proxy server-side Next.js.

## 2. Link Production Web UI

- URL: https://mycoffeemate.vercel.app/

Gunakan URL ini sebagai entry point utama untuk demo dan validasi user flow.

## 3. Arsitektur Produksi

### Komponen

- Frontend: Next.js (Vercel)
- Proxy route: `frontend/app/api/chat/route.ts`
- Backend: FastAPI (`backend/web_api/main.py`) di Render/Railway/Fly
- Vector store: ChromaDB (`data/vector_store/chroma_db`)

### Request Flow

1. User membuka `https://mycoffeemate.vercel.app/`.
2. UI mengirim `POST /api/chat` ke Next.js route.
3. Route Next.js mem-forward ke backend (`BACKEND_API_URL`).
4. Backend validasi token (jika aktif), rate limit per menit, dan daily cap per IP.
5. Backend menjalankan RAG (`Retriever` + `Generator`) lalu return `answer` + `sources`.
6. Route Next.js meneruskan response ke browser.

## 4. Konfigurasi Environment

### Backend (service FastAPI)

Wajib:
- `GROQ_API_KEY`
- `JINA_API_KEY`

Disarankan:
- `API_ACCESS_TOKEN`
- `RATE_LIMIT_PER_MINUTE=20`
- `DAILY_REQUEST_LIMIT_PER_IP=300`
- `ALLOWED_ORIGINS=https://rag-system-coffeeshop.vercel.app,http://localhost:3000,http://127.0.0.1:3000`

Opsional:
- `JINA_EMBEDDING_URL` jika endpoint embedding ingin diubah.

### Frontend (Vercel Project Environment Variables)

- `BACKEND_API_URL=https://<your-backend-domain>/api/chat`
- `BACKEND_API_TOKEN=<same value as API_ACCESS_TOKEN backend>`

Catatan:
- `BACKEND_API_TOKEN` tetap aman karena dipakai di server-side route Next.js.
- Tidak perlu menaruh token backend di `NEXT_PUBLIC_*`.

## 5. Rencana Deploy (Rombak dari Nol)

### Phase A - Backend First

1. Push repository ke Git provider.
2. Buat service backend Python.
3. Build command:
   - `pip install -r requirements.txt`
4. Start command:
   - `uvicorn backend.web_api.main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables backend (section 4).
6. Jika platform mendukung volume, mount volume untuk `data/vector_store/chroma_db`.
7. Verifikasi endpoint backend:
   - `GET /health` harus `service_ready: true`
   - `POST /api/chat` merespons 200 untuk pertanyaan valid

### Phase B - Frontend on Vercel

1. Import project ke Vercel.
2. Set root directory ke `frontend`.
3. Framework auto-detect: Next.js.
4. Isi env frontend:
   - `BACKEND_API_URL`
   - `BACKEND_API_TOKEN`
5. Deploy.
6. Uji dari domain Vercel production.

### Phase C - Integrasi Domain, CORS, dan Keamanan

1. Pastikan domain final frontend sudah benar: `https://mycoffeemate.vercel.app`.
2. Tambahkan domain itu ke `ALLOWED_ORIGINS` backend.
3. Redeploy backend agar setting CORS terbaru aktif.
4. Verifikasi behavior:
   - token invalid -> 401
   - burst request -> 429
   - traffic normal -> 200

## 6. Verifikasi Pasca Deploy

Checklist fungsional:
- [ ] Home page production dapat diakses.
- [ ] Chat request sukses dari UI.
- [ ] Response berisi `answer` dan `sources`.
- [ ] Tidak ada error CORS.

Checklist keamanan:
- [ ] Token backend tidak muncul di browser devtools client payload.
- [ ] Rate limit per menit bekerja.
- [ ] Daily limit (`DAILY_REQUEST_LIMIT_PER_IP`) bekerja.

Checklist observability:
- [ ] Log backend merekam latency request.
- [ ] Log error 5xx mudah dilacak.
- [ ] Event 401 dan 429 bisa dipantau frekuensinya.

## 7. Operasional Harian

- Rotasi token:
  1. Ubah `API_ACCESS_TOKEN` di backend.
  2. Ubah `BACKEND_API_TOKEN` di Vercel.
  3. Redeploy frontend dan backend.

- Update data:
  1. Perbarui source CSV processed.
  2. Jalankan `python scripts/reingest.py`.
  3. Pastikan vector store baru termuat.

- Jika instance backend ephemeral:
  - Pastikan file CSV sumber tersedia saat startup.
  - Pastikan `JINA_API_KEY` valid agar auto rebuild vector store dapat berjalan.

## 8. Risiko dan Mitigasi

- Risiko: in-memory limiter tidak sinkron di multi-instance.
  - Mitigasi: migrasi limiter ke Redis/distributed counter.

- Risiko: startup lambat karena rebuild vector store saat storage kosong.
  - Mitigasi: gunakan persistent volume dan prewarm service.

- Risiko: ketergantungan API eksternal (Jina/Groq) menyebabkan latency fluktuatif.
  - Mitigasi: monitor timeout, retry, dan fallback response.

## 9. Tempat Gambar Web UI

Direktori yang disiapkan:

- `docs/assets/web-ui/`

Disarankan simpan screenshot dengan pola nama:
- `01-home.png`
- `02-chat-result.png`
- `03-mobile-view.png`

Contoh pemakaian di markdown:

```md
## Web UI Screenshot

![Home](assets/web-ui/01-home.png)
![Chat Result](assets/web-ui/02-chat-result.png)
![Mobile View](assets/web-ui/03-mobile-view.png)
```

## 10. Referensi Cepat

- Web UI Production: https://mycoffeemate.vercel.app/
- Backend endpoint (contoh): `https://<backend-domain>/api/chat`
- Health check: `https://<backend-domain>/health`
