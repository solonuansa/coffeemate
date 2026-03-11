import re
import logging
import pandas as pd
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_chroma import Chroma
from backend.src.embed import EmbeddingModel
from backend.config.settings import VECTOR_STORE_DIR, EMBEDDING_MODEL, PROCESSED_DATA_DIR, INGEST_BATCH_SIZE

logger = logging.getLogger(__name__)


class DataIngestor:
    """Menangani loading dan ingest dokumen ke ChromaDB"""
    
    def __init__(self):
        """Inisialisasi data ingestor"""
        self.embedding_model = EmbeddingModel(EMBEDDING_MODEL)
        self.embedding_function = self._create_embedding_function()
        VECTOR_STORE_DIR.parent.mkdir(parents=True, exist_ok=True)
    
    def _create_embedding_function(self):
        """Buat fungsi embedding yang kompatibel dengan Chroma"""
        class EmbeddingWrapper:
            def __init__(self, model):
                self.model = model
            
            def embed_documents(self, texts):
                """Embed dokumen dengan prefix 'passage:'"""
                texts = [f"passage: {t}" for t in texts]
                return self.model.embed_texts(texts)
            
            def embed_query(self, text):
                """Embed query dengan prefix 'query:'"""
                return self.model.embed_text(f"query: {text}")
        
        return EmbeddingWrapper(self.embedding_model)
    
    def _clean_text(self, text: str) -> str:
        """Membersihkan teks"""
        if pd.isna(text):
            return ""
        text = str(text)
        text = re.sub(r"\s+", " ", text)  # Hapus spasi berlebih
        return text.strip()
    
    def _build_content(self, row: pd.Series) -> str:
        """Membangun content field dari baris data"""
        return f"""Kategori: {row['kategori']}
Lokasi: {row['lokasi']}
Sumber: {row['source']}

Deskripsi:
{row['deskripsi']}

Opini:
{row['opini']}"""
    
    def load_and_ingest_csv(self, csv_path: str):
        """
        Memuat dan ingest data dari CSV Sahabat AI
        
        Args:
            csv_path: Path ke file extracted_data_sahabatai.csv
        """
        csv_path = Path(csv_path)
        
        if not csv_path.exists():
            raise FileNotFoundError(f"File tidak ditemukan: {csv_path}")
        
        print(f"Memuat data dari: {csv_path}")
        
        # Load CSV
        df = pd.read_csv(csv_path)
        print(f"✓ Berhasil memuat {len(df)} baris data")
        print()
        
        # Validate required columns
        required_columns = ['Kota', 'Akun Instagram', 'Kategori Tempat', 'deskripsi', 'opini']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(
                f"Kolom yang dibutuhkan tidak ditemukan dalam CSV: {missing_columns}\n"
                f"Kolom yang tersedia: {list(df.columns)}"
            )
        
        # Pilih kolom yang diperlukan
        df = df[required_columns]
        
        # Rename kolom
        df.columns = ['lokasi', 'source', 'kategori', 'deskripsi', 'opini']
        
        # Tambahkan ID
        df.insert(0, 'id', range(1, 1 + len(df)))
        
        # Cleaning
        print("Membersihkan data...")
        for col in ["kategori", "lokasi", "source", "deskripsi", "opini"]:
            df[col] = df[col].apply(self._clean_text)
        
        # Build content
        print("Membangun content field...")
        df["content"] = df.apply(self._build_content, axis=1)
        
        # Convert to LangChain Documents
        print("Mengkonversi ke LangChain documents...")
        documents = []
        for _, row in df.iterrows():
            documents.append(
                Document(
                    page_content=row["content"],
                    metadata={
                        "id": row["id"],
                        "kategori": row["kategori"],
                        "lokasi": row["lokasi"],
                        "source": row["source"],
                    },
                )
            )
        
        print(f"Total {len(documents)} dokumen siap untuk di-embed")
        print()
        
        # Ingest ke Chroma
        print("Menyimpan ke ChromaDB")
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_function,
            persist_directory=str(VECTOR_STORE_DIR)
        )
        
        # Data otomatis tersimpan ke persist_directory
        print(f"Ingest selesai! {len(documents)} dokumen berhasil disimpan")
        print(f"Vector store tersimpan di: {VECTOR_STORE_DIR}")
