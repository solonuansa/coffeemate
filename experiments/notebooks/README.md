# Notebooks Experiments

Folder ini berisi notebook eksplorasi dan eksperimen untuk pipeline data sebelum masuk ke sistem RAG production.

## Isi Notebook

- `preprocessing.ipynb`
  - Eksperimen pembersihan teks, normalisasi, dan penyiapan dataset awal.

- `eda.ipynb`
  - Exploratory Data Analysis untuk melihat distribusi data, pola konten, dan kualitas data.

- `extract-referensikopi.ipynb`
  - Eksperimen ekstraksi data referensi coffee shop dari sumber mentah.

- `lda.ipynb`
  - Eksperimen topic modeling (LDA) untuk melihat kategori/topik dominan.

- `knowledge_base.ipynb`
  - Eksperimen penyusunan knowledge base yang menjadi dasar ingest ke vector store.

## Catatan

- Notebook di folder ini bersifat eksperimen, bukan entry point aplikasi production.
- Pipeline runtime utama berada di folder `backend/`, `scripts/`, dan `frontend/`.
