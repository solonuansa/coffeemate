import logging
import time
from typing import List

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

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Menangani embedding teks menggunakan Jina Embeddings API."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Inisialisasi embedding client.

        Args:
            model_name: Nama model embedding Jina.
        """
        self.model_name = model_name
        self.api_url = JINA_EMBEDDING_URL
        self.api_key = JINA_API_KEY

        if not self.api_key:
            raise ValueError("JINA_API_KEY tidak ditemukan. Silakan set di environment variables.")

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
        )
        print(f"Embedding provider aktif: Jina API ({self.model_name})")

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        payload = {
            "model": self.model_name,
            "input": texts,
        }

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self._session.post(
                    self.api_url,
                    json=payload,
                    timeout=API_TIMEOUT,
                )
                response.raise_for_status()
                body = response.json()
                data = body.get("data", [])

                if len(data) != len(texts):
                    raise ValueError(
                        f"Jumlah embedding tidak sesuai. expected={len(texts)} got={len(data)}"
                    )

                # Jina API mengembalikan index per item; urutkan untuk menjaga alignment.
                data = sorted(data, key=lambda item: item.get("index", 0))
                return [item["embedding"] for item in data]
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2**attempt)
                    logger.warning(
                        "Embedding API gagal (attempt %s/%s), retry in %s detik: %s",
                        attempt + 1,
                        MAX_RETRIES,
                        wait_time,
                        exc,
                    )
                    time.sleep(wait_time)
                else:
                    break

        raise RuntimeError(f"Gagal mengambil embedding dari Jina API: {last_error}")

    def embed_text(self, text: str) -> List[float]:
        """
        Embed satu teks.

        Args:
            text: Teks yang akan di-embed.

        Returns:
            Vector embedding.
        """
        return self._embed_batch([text])[0]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed beberapa teks sekaligus.

        Args:
            texts: List teks yang akan di-embed.

        Returns:
            List vector embedding.
        """
        if not texts:
            return []

        vectors: List[List[float]] = []
        for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[i : i + EMBEDDING_BATCH_SIZE]
            vectors.extend(self._embed_batch(batch))
        return vectors
