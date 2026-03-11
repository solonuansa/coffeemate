import logging
from langchain_community.vectorstores import Chroma
from backend.src.embed import EmbeddingModel
from backend.config.settings import VECTOR_STORE_DIR, EMBEDDING_MODEL, TOP_K_RESULTS, SCORE_THRESHOLD

logger = logging.getLogger(__name__)


class Retriever:
    """Menangani retrieval dokumen dari ChromaDB"""
    
    def __init__(self):
        """Inisialisasi retriever"""
        print("Memuat vector store...")
        
        # Validate vector store exists
        if not VECTOR_STORE_DIR.exists():
            raise FileNotFoundError(
                f"Vector store tidak ditemukan di {VECTOR_STORE_DIR}. "
                "Jalankan 'python scripts/reingest.py' terlebih dahulu untuk membuat vector store."
            )
        
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
                raise ValueError("Vector store kosong. Jalankan 'python scripts/reingest.py' untuk mengisi data.")
            print(f"Vector store berhasil dimuat ({doc_count} dokumen)")
        except Exception as e:
            raise RuntimeError(f"Gagal memuat vector store: {str(e)}")
    
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
            context += f"--- Sumber {i} ---\n"
            context += doc["content"]
            context += f"\n(Sumber: {doc['metadata'].get('source', 'Unknown')})\n\n"
        
        return context
