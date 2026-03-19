import logging
from backend.config.settings import (
    VECTOR_STORE_DIR,
    EMBEDDING_MODEL,
    TOP_K_RESULTS,
    SCORE_THRESHOLD,
    PROCESSED_DATA_DIR,
)
from langchain_chroma import Chroma

from backend.src.embed import EmbeddingModel

logger = logging.getLogger(__name__)


class Retriever:
    """Menangani retrieval dokumen dari ChromaDB"""
    
    def __init__(self):
        """Inisialisasi retriever"""
        print("Memuat vector store...")

        self._ensure_vector_store()

        # Load embedding model
        self.embedding_model = EmbeddingModel(EMBEDDING_MODEL)
        self.embedding_function = self._create_embedding_function()
        
        # Load vector store
        try:
            self.vectorstore = Chroma(
                persist_directory=str(VECTOR_STORE_DIR),
                embedding_function=self.embedding_function
            )
            doc_count = self.vectorstore._collection.count()
            if doc_count == 0:
                self._rebuild_vector_store()
                self.vectorstore = Chroma(
                    persist_directory=str(VECTOR_STORE_DIR),
                    embedding_function=self.embedding_function
                )
                doc_count = self.vectorstore._collection.count()
                if doc_count == 0:
                    raise ValueError("Vector store kosong setelah rebuild.")
            print(f"Vector store berhasil dimuat ({doc_count} dokumen)")
        except Exception as e:
            raise RuntimeError(f"Gagal memuat vector store: {str(e)}")

    def _ensure_vector_store(self) -> None:
        """Pastikan vector store tersedia sebelum dipakai."""
        if VECTOR_STORE_DIR.exists():
            return
        self._rebuild_vector_store()

    def _rebuild_vector_store(self) -> None:
        """
        Build ulang vector store dari CSV processed.

        Ini penting untuk environment ephemeral seperti Railway.
        """
        csv_path = PROCESSED_DATA_DIR / "extracted_data_sahabatai.csv"
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Vector store tidak ditemukan di {VECTOR_STORE_DIR}, "
                f"dan file sumber juga tidak ditemukan di {csv_path}."
            )

        logger.info(
            "Vector store belum tersedia/invalid, membangun ulang dari %s",
            csv_path,
        )
        from backend.src.ingest import DataIngestor

        ingestor = DataIngestor()
        ingestor.load_and_ingest_csv(str(csv_path))
    
    def _create_embedding_function(self):
        """Buat fungsi embedding yang kompatibel dengan Chroma"""
        class EmbeddingWrapper:
            def __init__(self, model):
                self.model = model
            
            def embed_documents(self, texts):
                texts = [f"passage: {t}" for t in texts]
                return self.model.embed_texts(texts)
            
            def embed_query(self, text):
                return self.model.embed_text(f"query: {text}")
        
        return EmbeddingWrapper(self.embedding_model)
    
    def retrieve(self, query: str, k: int = TOP_K_RESULTS) -> list:
        """
        Retrieve dokumen relevan berdasarkan query menggunakan MMR dan score threshold
        
        Args:
            query: Query dari user
            k: Jumlah dokumen yang diambil (default dari settings)
            
        Returns:
            List dokumen relevan
        """
        # Gunakan MMR untuk diversity (ambil lebih banyak dulu)
        fetch_k = k * 2  # Ambil 2x lebih banyak untuk diversity
        results = self.vectorstore.max_marginal_relevance_search(
            query, 
            k=k, 
            fetch_k=fetch_k
        )
        
        # Format ke dict untuk kompatibilitas
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in results
        ]
    
    def retrieve_with_threshold(self, query: str, k: int = TOP_K_RESULTS, threshold: float = SCORE_THRESHOLD) -> list:
        """
        Retrieve dokumen relevan dengan score threshold untuk memfilter hasil berkualitas rendah
        
        Args:
            query: Query dari user
            k: Jumlah dokumen yang diambil (default dari settings)
            threshold: Threshold untuk memfilter hasil (semakin kecil semakin ketat)
            
        Returns:
            List dokumen relevan yang lolos threshold
        """
        # Ambil lebih banyak dokumen untuk filtering
        fetch_k = k * 3
        results_with_scores = self.vectorstore.similarity_search_with_score(
            query, 
            k=fetch_k
        )
        
        # Filter berdasarkan threshold
        filtered_results = [
            (doc, score) for doc, score in results_with_scores 
            if score < threshold
        ]
        
        # Ambil k hasil terbaik
        filtered_results = filtered_results[:k]
        
        # Format ke dict untuk kompatibilitas
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            }
            for doc, score in filtered_results
        ]

    def retrieve_with_threshold_diagnostics(
        self,
        query: str,
        k: int = TOP_K_RESULTS,
        threshold: float = SCORE_THRESHOLD,
    ) -> tuple[list, list]:
        """
        Retrieve dokumen dengan threshold dan sertakan dokumen yang disisihkan.

        Returns:
            tuple(accepted_docs, rejected_docs)
        """
        fetch_k = k * 3
        results_with_scores = self.vectorstore.similarity_search_with_score(
            query,
            k=fetch_k,
        )

        accepted = []
        rejected = []
        for doc, score in results_with_scores:
            item = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score,
            }
            if score < threshold and len(accepted) < k:
                accepted.append(item)
            else:
                rejected.append(item)

        return accepted, rejected
    
    def format_context(self, documents: list) -> str:
        """
        Format dokumen menjadi context string
        
        Args:
            documents: List dokumen
            
        Returns:
            Formatted context string
        """
        if not documents:
            return "Tidak ada dokumen relevan ditemukan."
        
        context = "Informasi Relevan:\n\n"
        for i, doc in enumerate(documents, 1):
            metadata = doc.get("metadata", {})
            source = metadata.get("source", "Unknown")
            lokasi = metadata.get("lokasi", "Unknown")
            context += f"--- Sumber {i} ---\n"
            context += f"Nama Referensi: {source}\n"
            context += f"Lokasi Referensi: {lokasi}\n"
            context += doc["content"]
            context += f"\n(Sumber: {source})\n\n"

        return context
