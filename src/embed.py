import logging
from typing import List

from sentence_transformers import SentenceTransformer

from config.settings import EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Menangani embedding teks menggunakan sentence transformers."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Inisialisasi model embedding.

        Args:
            model_name: Nama model sentence transformer.
        """
        print(f"Memuat model embedding: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("Model embedding berhasil dimuat")

    def embed_text(self, text: str) -> List[float]:
        """
        Embed satu teks.

        Args:
            text: Teks yang akan di-embed.

        Returns:
            Vector embedding.
        """
        return self.model.encode(text).tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed beberapa teks sekaligus.

        Args:
            texts: List teks yang akan di-embed.

        Returns:
            List vector embedding.
        """
        return self.model.encode(texts).tolist()
