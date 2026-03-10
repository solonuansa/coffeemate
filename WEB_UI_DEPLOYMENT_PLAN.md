# Web UI and Deployment Plan - Next.js + FastAPI

## 1. Tujuan
- Membangun UI web dengan React yang bagus, terstruktur, dan interaktif.
- Memisahkan concern frontend dan backend agar mudah scale.
- Menjaga pipeline RAG existing tetap dipakai tanpa rewrite besar.

## 2. Keputusan Teknologi
- Frontend: `Next.js` (React, App Router, TypeScript).
- Backend API: `FastAPI` (tetap Python, reuse logic RAG sekarang).
- Vector DB awal: `ChromaDB` (tetap dipakai untuk fase MVP).
- Styling: CSS Modules atau Tailwind (pilih satu, default rekomendasi: Tailwind untuk kecepatan).

## 3. Kenapa Next.js
- Struktur project jelas untuk page, layout, komponen, dan API integration.
- DX bagus untuk komponen interaktif (chat UI, source cards, state handling).
- Mudah deploy frontend ke Vercel.
- Mendukung optimasi produksi (bundling, caching, image/font optimization).

## 4. Scope Fitur MVP
- Chat interface dengan message history.
- Input multi-line dengan keyboard shortcut (`Enter` kirim, `Shift+Enter` newline).
- Panel sumber per jawaban (`nama`, `lokasi`).
- Loading/typing indicator.
- Error state + tombol retry.
- Simpan sesi chat di `sessionStorage`.

## 5. UX/UI Spesifikasi
- Layout 3 area: header, chat timeline, input dock.
- Visual hierarchy kuat:
  - user bubble dan assistant bubble beda jelas,
  - source cards ditampilkan terstruktur di bawah jawaban.
- Interaktif:
  - optimistic render untuk pesan user,
  - auto-scroll ke pesan terbaru,
  - transisi ringan saat pesan baru muncul.
- Responsive:
  - mobile first,
  - sticky input di bawah layar.

## 6. Arsitektur Sistem
- Frontend Next.js memanggil backend FastAPI via REST.
- FastAPI expose endpoint:
  - `POST /api/chat`
  - `GET /health`
- Service layer backend:
  - `src/rag_service.py` untuk orkestrasi retriever + generator.
- Gunakan schema request/response konsisten:
  - request: `{"question": "..."}`.
  - response: `{"answer": "...", "sources": [{"nama": "...", "lokasi": "..."}]}`.

## 7. Rencana Implementasi Bertahap

### Phase 1 - Backend API Stabil (Hari 1)
- Refactor logic dari `app.py` ke `src/rag_service.py`.
- Buat FastAPI app khusus API (mis. `web_api/main.py`).
- Tambah validasi input, exception handling, logging durasi query.
- Tambah CORS untuk domain frontend.

### Phase 2 - Setup Frontend Next.js (Hari 2)
- Inisialisasi Next.js + TypeScript.
- Buat struktur folder:
  - `app/`
  - `components/`
  - `lib/`
  - `types/`
- Buat service client untuk memanggil backend chat API.

### Phase 3 - UI Chat Interaktif (Hari 3)
- Implement komponen:
  - `ChatShell`
  - `MessageList`
  - `MessageBubble`
  - `SourcesPanel`
  - `ChatInput`
- Tambah state management lokal dengan reducer/hook custom.
- Tambah loading, error, retry, dan session persistence.

### Phase 4 - Polish dan Aksesibilitas (Hari 4)
- Rapikan design token (warna, radius, spacing, typography).
- Perbaiki kontras, keyboard navigation, focus state, ARIA label.
- Tambah empty state dan helper text yang jelas.

### Phase 5 - Testing dan Hardening (Hari 5)
- Uji skenario sukses, gagal, timeout, query kosong, query panjang.
- Basic test frontend (komponen utama) dan backend endpoint.
- Dokumentasi run local + env setup + troubleshooting.

## 8. Struktur Folder Target
```text
RAG/
  web-api/
    main.py
  src/
    rag_service.py
  frontend/
    app/
    components/
    lib/
    types/
    public/
    package.json
```

## 9. Deployment Strategy

### Frontend
- Deploy `Next.js` ke Vercel.
- Set environment variable `NEXT_PUBLIC_API_BASE_URL` ke URL backend FastAPI.

### Backend
- Deploy FastAPI ke Render, Railway, atau Fly.io (server penuh/non-serverless disarankan).
- Mount persistent volume jika ChromaDB file tetap dipakai.
- Set env var `GROQ_API_KEY` di platform backend.

### Kenapa Tidak Full di Vercel
- Vercel serverless kurang cocok untuk RAG backend berbasis Python + local vector store persistence.
- Risiko timeout dan cold start lebih tinggi.
- File system ephemeral menyulitkan penyimpanan ChromaDB jangka panjang.

## 10. Vector DB Decision: Chroma vs FAISS vs PostgreSQL

### Rekomendasi Saat Ini
- Tetap pakai `ChromaDB` untuk MVP.
- Tidak perlu pindah ke FAISS sekarang.
- Siapkan jalur migrasi ke `PostgreSQL + pgvector` saat kebutuhan naik.

### Kapan Tetap ChromaDB
- Single app, traffic masih rendah-menengah.
- Fokus cepat release.
- Metadata filtering belum kompleks.

### Kapan Migrasi ke PostgreSQL + pgvector
- Mulai butuh reliability produksi (backup, restore, durability).
- Butuh query metadata lebih kompleks.
- Mulai ada multi-user dan kebutuhan observability/data governance.

### Posisi FAISS
- FAISS bagus untuk eksperimen retrieval cepat.
- Kurang ideal sebagai database produksi utama dibanding PostgreSQL+pgvector untuk use case aplikasi web.

## 11. Roadmap Migrasi Database (Jika Diperlukan)
- Tahap 1: abstraksikan layer vector store (`VectorStoreRepository` interface).
- Tahap 2: implement adapter `ChromaRepository`.
- Tahap 3: implement adapter `PgVectorRepository`.
- Tahap 4: dual-run evaluasi kualitas retrieval.
- Tahap 5: cutover bertahap ke pgvector.

## 12. Checklist Eksekusi
- [ ] Refactor service RAG untuk API-first design.
- [ ] Implement FastAPI endpoint yang stabil.
- [ ] Setup Next.js frontend.
- [ ] Bangun UI chat yang interaktif dan responsive.
- [ ] Deploy frontend ke Vercel.
- [ ] Deploy backend ke Render/Railway/Fly.
- [ ] Monitoring dasar dan uji end-to-end.
