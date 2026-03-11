import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.src.ingest import DataIngestor
from backend.config.settings import VECTOR_STORE_DIR, PROCESSED_DATA_DIR


def reingest_data():
    """Ingest data Sahabat AI"""
    
    print("=" * 60)
    print("Ingest Data Sahabat AI ke ChromaDB")
    print("=" * 60)
    print()
    
    # 1. Hapus vector store lama (optional)
    if VECTOR_STORE_DIR.exists():
        print(f"Menghapus vector store lama...")
        shutil.rmtree(VECTOR_STORE_DIR)
        print("Vector store lama berhasil dihapus")
        print()
    
    # 2. Ingest data
    csv_path = PROCESSED_DATA_DIR / "extracted_data_sahabatai.csv"
    
    if not csv_path.exists():
        print(f"File tidak ditemukan: {csv_path}")
        return
    
    try:
        ingestor = DataIngestor()
        ingestor.load_and_ingest_csv(str(csv_path))
        
        print()
        print("=" * 60)
        print("Ingest selesai!")
        print("=" * 60)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    reingest_data()
