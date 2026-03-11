# Dokumentasi Kode Sistem RAG Coffee Shop

## Table of Contents
- [Overview Sistem](#overview-sistem)
- [Arsitektur Eksekusi](#arsitektur-eksekusi)
- [backend/config/settings.py](#backendconfigsettingspy)
- [backend/src/embed.py](#backendsrcembedpy)
- [backend/src/ingest.py](#backendsrcingestpy)
- [backend/src/retriever.py](#backendsrcretrieverpy)
- [backend/src/generator.py](#backendsrcgeneratorpy)
- [backend/src/rag_service.py](#backendsrcrag_servicepy)
- [backend/web_api/security.py](#backendweb_apisecuritypy)
- [backend/web_api/main.py](#backendweb_apimainpy)
- [scripts/reingest.py](#scriptsreingestpy)
- [scripts/cli.py](#scriptsclipy)
- [frontend/app/api/chat/route.ts](#frontendappapichatroutets)
- [Alur Data End-to-End](#alur-data-end-to-end)
- [Catatan Teknis Penting](#catatan-teknis-penting)

---

## Overview Sistem

Sistem ini adalah aplikasi RAG (Retrieval-Augmented Generation) untuk rekomendasi coffee shop berbasis data terstruktur dari CSV hasil ekstraksi Instagram. Komponen utama:

1. **Ingest**: data CSV dibersihkan, diformat, lalu disimpan ke ChromaDB sebagai dokumen vector.
2. **Retrieval**: query user dipetakan ke embedding, lalu dicari dokumen relevan dari Chroma.
3. **Generation**: konteks hasil retrieval dikirim ke model LLM (Groq) untuk menghasilkan jawaban natural.
4. **Delivery**: jawaban disajikan via FastAPI (`/api/chat`) dan dipakai oleh frontend Next.js melalui route proxy server-side.

Stack yang dipakai saat ini:
- Embedding: **Jina Embeddings API** (`jina-embeddings-v5-text-small`)
- Vector store: **ChromaDB** (persisted local directory)
- Generation: **Groq API** (`llama-3.3-70b-versatile`)
- API service: **FastAPI**
- Frontend: **Next.js**
- Data processing: **pandas**

---

## Arsitektur Eksekusi

Ada dua cara menjalankan sistem:

1. **Mode Web**
- Browser -> Next.js route `POST /api/chat`
- Next.js route -> forward ke FastAPI backend
- FastAPI -> validasi token/rate limit -> `RAGService.ask()`
- `RAGService` -> `Retriever` + `Generator`
- Response dikembalikan ke browser

2. **Mode CLI**
- User input di terminal
- `scripts/cli.py` memanggil `RAGService.ask()` langsung
- Hasil jawaban dan sumber dicetak ke terminal

Dengan pola ini, logika RAG terpusat di service layer yang sama untuk web dan CLI.

---

## backend/config/settings.py

File ini adalah pusat konfigurasi runtime: path data, model, API key, retry policy, parameter retrieval, dan policy keamanan API.

### Fungsi utama file
- Menentukan direktori penting (`BASE_DIR`, `VECTOR_STORE_DIR`, dll).
- Membaca environment variables dari `.env` root proyek.
- Menyediakan nilai default aman jika env belum diisi.
- Menjadi single source of truth untuk konstanta lintas modul.

### Blok path

```python
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RAW_DATA_DIR = DATA_DIR / "raw"
VECTOR_STORE_DIR = DATA_DIR / "vector_store" / "chroma_db"
```

Penjelasan:
- `parents[2]` memastikan root proyek terbaca benar dari `backend/config/settings.py`.
- `.env` diload sekali di level config agar modul lain tinggal import constants.
- `VECTOR_STORE_DIR` adalah lokasi persistence ChromaDB.

### Blok model dan API key

```python
EMBEDDING_MODEL = "jina-embeddings-v5-text-small"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
JINA_API_KEY = os.getenv("JINA_API_KEY", "")
JINA_EMBEDDING_URL = os.getenv("JINA_EMBEDDING_URL", "https://api.jina.ai/v1/embeddings")
```

Penjelasan:
- Sistem embedding sekarang tidak lagi `sentence-transformers` lokal, tetapi API Jina.
- `JINA_API_KEY` wajib ada untuk proses ingest dan retrieval.
- `GROQ_API_KEY` wajib ada untuk generation.

### Blok security API

```python
API_ACCESS_TOKEN = os.getenv("API_ACCESS_TOKEN", "")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
DAILY_REQUEST_LIMIT_PER_IP = int(os.getenv("DAILY_REQUEST_LIMIT_PER_IP", "300"))
ALLOWED_ORIGINS = [ ... ]
```

Penjelasan:
- `API_ACCESS_TOKEN` bersifat optional. Jika kosong, endpoint bisa diakses tanpa bearer token.
- `RATE_LIMIT_PER_MINUTE` dan `DAILY_REQUEST_LIMIT_PER_IP` dipakai oleh `InMemoryUsageGuard`.
- `ALLOWED_ORIGINS` diparse dari CSV string env, lalu dibersihkan dengan `.strip()`.

### Blok retrieval/generation/retry

```python
TOP_K_RESULTS = 5
SCORE_THRESHOLD = 0.3
MAX_TOKENS = 1024
TEMPERATURE = 0.7
API_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_DELAY = 2
```

Penjelasan:
- `TOP_K_RESULTS` digunakan pada retrieval default.
- `SCORE_THRESHOLD` dipakai di method retrieval alternatif berbasis similarity score.
- `MAX_RETRIES` + `RETRY_DELAY` dipakai di embedding call dan generation call untuk backoff.

### Prompt utama

`SYSTEM_PROMPT` berisi aturan output markdown yang ketat (bullet list nama tempat, detail di baris biasa, tidak menampilkan label sumber internal), sehingga format jawaban konsisten untuk UI.

---

## backend/src/embed.py

Modul ini mengelola koneksi ke Jina Embeddings API dan abstraksi embedding satu teks maupun batch.

### Dependensi penting

```python
import requests
from backend.config.settings import (
    API_TIMEOUT,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MODEL,
    JINA_API_KEY,
    JINA_EMBEDDING_URL,
    MAX_RETRIES,
    RETRY_DELAY,
)
```

Penjelasan:
- `requests.Session()` dipakai untuk reuse koneksi HTTP dan header.
- Timeout/retry mengikuti settings global agar konsisten lintas modul.

### Class `EmbeddingModel`

#### `__init__`

```python
self.model_name = model_name
self.api_url = JINA_EMBEDDING_URL
self.api_key = JINA_API_KEY
if not self.api_key:
    raise ValueError(...)
```

Penjelasan:
- Validasi API key dilakukan saat object dibuat, sehingga error muncul lebih awal.
- Session header menyertakan `Authorization: Bearer <JINA_API_KEY>`.

#### `_embed_batch(texts)`

Flow:
1. Bentuk payload:
   - `model`: nama model embedding
   - `input`: list teks
2. Lakukan request POST ke endpoint Jina.
3. Validasi HTTP status (`raise_for_status`).
4. Ambil `body["data"]` dan cek panjang hasil sama dengan jumlah input.
5. Urutkan berdasarkan field `index` agar alignment input-output aman.
6. Return list vektor.

Retry behavior:
- Jika gagal, logging warning + exponential backoff: `RETRY_DELAY * (2**attempt)`.
- Jika semua percobaan gagal, raise `RuntimeError` dengan error terakhir.

#### `embed_text(text)` dan `embed_texts(texts)`

- `embed_text` memanggil `_embed_batch([text])` lalu mengambil elemen pertama.
- `embed_texts` memecah input berdasarkan `EMBEDDING_BATCH_SIZE`, lalu menggabungkan hasil tiap batch.
- Jika input kosong, return list kosong.

---

## backend/src/ingest.py

Modul ini membangun pipeline ingest CSV -> LangChain `Document` -> ChromaDB persisted store.

### Struktur class

`DataIngestor` mengelola keseluruhan proses ingest.

#### `__init__`
- Membuat `EmbeddingModel`.
- Menyediakan adapter embedding function compatible dengan API Chroma (`embed_documents` dan `embed_query`).
- Memastikan parent directory vector store tersedia.

#### `_create_embedding_function()`

Class inner `EmbeddingWrapper`:
- `embed_documents(texts)`: menambahkan prefix `passage: ` ke setiap teks, lalu memanggil `embed_texts`.
- `embed_query(text)`: menambahkan prefix `query: ` lalu memanggil `embed_text`.

Alasan prefix:
- Menjaga konsistensi semantik query vs passage sesuai praktik retrieval modern.

#### `_clean_text(text)`
- Menangani nilai kosong (`NaN` -> string kosong).
- Menormalkan whitespace dengan regex `\s+` menjadi single space.
- Trim spasi depan/belakang.

#### `_build_content(row)`
Menyusun format content dokumen:
- `Kategori`
- `Lokasi`
- `Sumber`
- `Deskripsi`
- `Opini`

Format ini dipakai sebagai `page_content` agar konteks retrieval tetap kaya dan konsisten.

#### `load_and_ingest_csv(csv_path)`

Urutan detail:
1. Validasi file CSV ada.
2. `pd.read_csv` untuk load data.
3. Validasi kolom wajib:
   - `Kota`
   - `Akun Instagram`
   - `Kategori Tempat`
   - `deskripsi`
   - `opini`
4. Pilih kolom tersebut lalu rename jadi:
   - `lokasi`, `source`, `kategori`, `deskripsi`, `opini`
5. Tambah kolom `id` berurutan.
6. Cleaning text untuk semua field utama.
7. Build kolom `content` dari tiap row.
8. Konversi tiap row menjadi `Document` dengan metadata ringkas (`id`, `kategori`, `lokasi`, `source`).
9. Simpan ke Chroma via `Chroma.from_documents(..., persist_directory=VECTOR_STORE_DIR)`.

Output:
- Vector store persisten di `data/vector_store/chroma_db`.

---

## backend/src/retriever.py

Modul ini menangani loading vector store, fallback rebuild otomatis, retrieval, dan formatting context untuk generator.

### Inisialisasi retriever

Saat `Retriever()` dibuat:
1. Memastikan vector store ada (`_ensure_vector_store`).
2. Inisialisasi embedding model + wrapper.
3. Membuka Chroma dari `persist_directory`.
4. Cek jumlah dokumen koleksi.
5. Jika koleksi kosong, trigger `_rebuild_vector_store()` lalu load ulang.
6. Jika setelah rebuild masih kosong, raise error.

### `_ensure_vector_store()`
- Jika path vector store belum ada, langsung build dari CSV processed.

### `_rebuild_vector_store()`
- Sumber data default: `data/processed/extracted_data_sahabatai.csv`.
- Jika file tidak ada, raise `FileNotFoundError` yang eksplisit.
- Jika ada, instantiate `DataIngestor` dan jalankan ingest.

Catatan penting:
- Ini sangat berguna di platform dengan ephemeral filesystem (misalnya instance yang restart dan kehilangan local storage).

### Retrieval methods

#### `retrieve(query, k=TOP_K_RESULTS)`
- Menggunakan `max_marginal_relevance_search`.
- `fetch_k = k * 2` untuk diversity dokumen.
- Return list dict dengan format stabil:
  - `content`
  - `metadata`

#### `retrieve_with_threshold(query, k, threshold)`
- Menggunakan `similarity_search_with_score`.
- Ambil `fetch_k = k * 3`, lalu filter score `< threshold`.
- Return list dict yang juga menyertakan `score`.

#### `format_context(documents)`
- Jika dokumen kosong: return teks fallback.
- Jika ada dokumen: format menjadi blok konteks berurutan per sumber.

---

## backend/src/generator.py

Modul ini bertanggung jawab untuk call Groq API dan mengelola retry logic saat generation gagal.

### Inisialisasi

`Generator.__init__`:
- Memilih API key dari parameter atau settings default.
- Validasi `GROQ_API_KEY` wajib ada.
- Inisialisasi client `Groq(api_key=...)`.

### `generate(query, context, ...)`

Langkah kerja:
1. Build `user_message` dari `CONTEXT_PROMPT_TEMPLATE` dengan `context` dan `query`.
2. Panggil `client.chat.completions.create` dengan:
   - role `system` (pakai `SYSTEM_PROMPT`),
   - role `user` (konteks + pertanyaan),
   - model Groq,
   - token limit,
   - temperature,
   - timeout.
3. Ambil `choices[0].message.content`.

Error handling:
- `RateLimitError`: retry dengan backoff, jika gagal total return pesan batas permintaan.
- `APIError`: retry dengan backoff, jika gagal total return pesan error API.
- Exception umum: retry dengan backoff, jika gagal total return teks error.

### `generate_simple(prompt, max_tokens)`
- Varian tanpa sistem prompt + konteks retrieval.
- Dipertahankan untuk kebutuhan prompt langsung/non-RAG.

---

## backend/src/rag_service.py

Ini adalah orchestration layer inti yang dipakai oleh FastAPI dan CLI.

### Tujuan desain
- Menyatukan alur retrieval + generation di satu class reusable.
- Menjaga web layer (`main.py`) tetap tipis.

### `RAGService.ask(question)`

Urutan:
1. Trim input.
2. Validasi tidak boleh kosong (`ValueError`).
3. Panggil `retriever.retrieve(question)`.
4. Jika hasil kosong, return jawaban fallback + sumber kosong.
5. Bangun context lewat `retriever.format_context(documents)`.
6. Generate jawaban lewat `generator.generate(question, context)`.
7. Ekstrak sumber via `_extract_sources(documents)`.
8. Return object final:
   - `answer`
   - `sources` (list nama + lokasi)

### `_extract_sources(documents)`
- Mengambil metadata aman via `.get()` dengan fallback `Unknown`.

---

## backend/web_api/security.py

Modul guard in-memory untuk rate limit menit dan daily cap per IP.

### Data model

`RateLimitResult` (dataclass):
- `allowed`: bool
- `detail`: pesan hasil validasi
- `retry_after_seconds`: integer untuk header `Retry-After`

### Class `InMemoryUsageGuard`

State internal:
- `_minute_windows`: `Dict[ip, deque[timestamp]]`
- `_daily_counts`: `Dict[(ip, date), int]`
- `_lock`: `threading.Lock` untuk thread safety

### `check_and_consume(client_ip)`

Urutan logika:
1. Hapus timestamp lama di luar window 60 detik.
2. Jika jumlah request dalam window >= limit per menit, tolak request.
3. Cek total request harian untuk `(ip, today)`.
4. Jika sudah mencapai batas harian, tolak request.
5. Jika lolos, konsumsi 1 request (append timestamp + increment daily count).

Catatan:
- Cocok untuk single process.
- Untuk multi-instance/multi-worker, perlu backend shared storage (misalnya Redis).

---

## backend/web_api/main.py

Ini entry point FastAPI API publik untuk frontend/web client.

### Komponen penting

- `MAX_QUESTION_LENGTH = 500`
- Global singleton-like objects:
  - `rag_service`
  - `startup_error`
  - `usage_guard`

### Model request/response

- `ChatRequest`: field `question` wajib, panjang 1..500.
- `SourceItem`: `nama`, `lokasi`.
- `ChatResponse`: `answer`, `sources`.

### Lifespan startup

Pada startup app:
- `RAGService()` diinisialisasi.
- Jika gagal, error disimpan di `startup_error` dan endpoint akan merespons `503`.

### Middleware

1. `CORSMiddleware` dengan origin dari settings.
2. Middleware security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Cache-Control: no-store`

### Helper functions

- `get_client_ip(request)`:
  - prioritas `x-forwarded-for`, fallback `request.client.host`.
- `enforce_access_token(request)`:
  - aktif hanya jika `API_ACCESS_TOKEN` di-set.
  - memvalidasi header exact match `Bearer <token>`.

### Endpoint `GET /health`

Return:
- `status` (`ok`/`error`)
- `service_ready`
- `error` (isi `startup_error` bila gagal startup)

### Endpoint `POST /api/chat`

Alur detail:
1. Pastikan service siap, kalau tidak return `503`.
2. Validasi bearer token (jika aktif).
3. Ambil client IP.
4. Jalankan `usage_guard.check_and_consume`.
5. Jika limit terlampaui, return `429` + header `Retry-After`.
6. Trim dan validasi pertanyaan.
7. Catat `started_at` untuk logging latency.
8. Panggil `rag_service.ask(question)`.
9. Return hasil jika sukses.
10. Tangani error:
- `ValueError` -> `422`
- exception lain -> `500` dengan pesan generic.

---

## scripts/reingest.py

Script utilitas untuk rebuild vector store dari awal.

### Urutan kerja

1. Cek apakah `VECTOR_STORE_DIR` ada.
2. Jika ada, hapus direktori vector store lama dengan `shutil.rmtree`.
3. Tentukan path CSV default: `PROCESSED_DATA_DIR / "extracted_data_sahabatai.csv"`.
4. Jika CSV tidak ada, print pesan lalu stop.
5. Jika ada, jalankan `DataIngestor().load_and_ingest_csv(...)`.
6. Print status selesai atau error.

Use case:
- Digunakan saat data source berubah dan ingin reindex penuh.

---

## scripts/cli.py

Entry point interaktif terminal untuk menggunakan RAG tanpa web.

### Inisialisasi awal

- Load `.env` dari root project.
- Menambahkan root project ke `sys.path` agar import backend stabil.
- Mengatur warning dan logging agar output CLI lebih bersih.

### Class `RAGApp`

- `__init__`: inisialisasi `RAGService`.
- `query(question)`: cetak query lalu delegasi ke `RAGService.ask`.
- `print_response(response)`: menampilkan jawaban dan daftar sumber.

### `main()`

1. Validasi `GROQ_API_KEY` tersedia.
2. Inisialisasi `RAGApp` dengan error handling.
3. Masuk loop interaktif input user.
4. Handle command keluar (`exit`, `quit`).
5. Validasi panjang pertanyaan maksimum 500 karakter.
6. Jalankan query dan tampilkan hasil.
7. Tangani `KeyboardInterrupt` agar keluar dengan graceful.

---

## frontend/app/api/chat/route.ts

Route handler server-side di Next.js yang berfungsi sebagai proxy aman dari browser ke backend FastAPI.

### Konfigurasi runtime

```ts
const BACKEND_API_URL = process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000/api/chat";
const BACKEND_API_TOKEN = process.env.BACKEND_API_TOKEN ?? "";
const MAX_QUESTION_LENGTH = 500;
```

Penjelasan:
- URL backend dan token tidak diekspos ke client karena route ini berjalan di server Next.js.
- Validasi panjang pertanyaan diselaraskan dengan backend.

### Flow handler `POST`

1. Parse body JSON.
2. Trim `question`.
3. Validasi kosong dan batas panjang.
4. Siapkan header ke backend (`Content-Type`, optional `Authorization`).
5. Forward request dengan `fetch` + `cache: "no-store"`.
6. Ambil payload response backend.
7. Return payload dengan status backend asli.
8. Jika exception internal route, return `500` generic.

Manfaat arsitektur ini:
- Browser tidak perlu tahu token backend.
- Endpoint backend bisa diproteksi tanpa membuka credential di frontend client.

---

## Alur Data End-to-End

### Alur ingest data

1. CSV di `data/processed/extracted_data_sahabatai.csv`.
2. `DataIngestor` membersihkan dan memformat data.
3. Data diubah jadi `Document` LangChain.
4. Embedding dipanggil via Jina API.
5. Dokumen tersimpan ke ChromaDB persisted directory.

### Alur query web

1. User kirim pertanyaan dari UI.
2. Next.js route memvalidasi dasar lalu forward ke backend.
3. Backend melakukan auth + rate limit + daily limit.
4. `RAGService.ask` menjalankan retrieval dan generation.
5. Backend mengembalikan jawaban + sumber.
6. Next.js meneruskan response ke browser.

### Alur fallback startup

Jika vector store hilang/kosong:
1. `Retriever` mendeteksi kondisi tersebut saat inisialisasi.
2. `Retriever` otomatis memanggil ingest dari CSV.
3. Sistem lanjut startup tanpa langkah manual tambahan, selama CSV dan API key Jina tersedia.

---

## Catatan Teknis Penting

1. **Kebutuhan API key**
- `GROQ_API_KEY` wajib untuk generation.
- `JINA_API_KEY` wajib untuk embedding ingest/retrieval.

2. **Batas pertanyaan**
- Backend dan frontend sama-sama membatasi `question` maksimal 500 karakter.

3. **Limiter saat ini**
- In-memory guard cocok untuk single process.
- Untuk skala multi-instance, pindah ke Redis/distributed store.

4. **Konsistensi embedding**
- Ingest dan retrieval wajib memakai provider/model embedding yang sama.

5. **Reliability**
- Embedding dan generation sama-sama memiliki retry + exponential backoff.

6. **Kualitas context**
- `format_context` di retriever masih menyertakan label sumber internal.
- Prompt sistem secara eksplisit meminta model tidak menampilkan label tersebut di jawaban akhir.
