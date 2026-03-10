import logging
from typing import Any, Dict, List

from src.generator import Generator
from src.retriever import Retriever

logger = logging.getLogger(__name__)


class RAGServiceError(Exception):
    """Base exception for RAG service errors."""


class RAGService:
    """Reusable service layer for RAG query orchestration."""

    def __init__(self) -> None:
        self.retriever = Retriever()
        self.generator = Generator()

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Process a user question with retrieval and generation.

        Args:
            question: User query.

        Returns:
            A response dictionary with answer and sources.
        """
        question = question.strip()
        if not question:
            raise ValueError("Question tidak boleh kosong.")

        documents = self.retriever.retrieve(question)
        if not documents:
            return {
                "answer": "Maaf, tidak ada informasi yang relevan ditemukan.",
                "sources": [],
            }

        context = self.retriever.format_context(documents)
        answer = self.generator.generate(question, context)
        sources = self._extract_sources(documents)

        return {
            "answer": answer,
            "sources": sources,
        }

    @staticmethod
    def _extract_sources(documents: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        sources: List[Dict[str, str]] = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            sources.append(
                {
                    "nama": metadata.get("source", "Unknown"),
                    "lokasi": metadata.get("lokasi", "Unknown"),
                }
            )
        return sources
