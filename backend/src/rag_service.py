import logging
import re
from typing import Any, Dict, List

from backend.src.generator import Generator
from backend.src.retriever import Retriever

logger = logging.getLogger(__name__)

UNSAFE_PROMPT_PATTERNS = [
    r"\bignore\b.{0,40}\b(instruction|system|aturan|perintah)\b",
    r"\b(jailbreak|prompt injection|dan\b mode)\b",
    r"\b(system prompt|developer message|hidden prompt)\b",
    r"\b(reveal|bocorkan|leak)\b.{0,40}\b(prompt|token|secret|api key|kunci)\b",
]

OUT_OF_SCOPE_REPLY = (
    "Maaf, saya hanya bisa membantu pertanyaan seputar rekomendasi coffee shop "
    "dan informasi terkait di wilayah Yogyakarta berdasarkan data yang tersedia."
)


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

        if self._looks_like_prompt_injection(question):
            return {
                "answer": OUT_OF_SCOPE_REPLY,
                "sources": [],
            }

        documents = self.retriever.retrieve_with_threshold(question)
        if not documents:
            return {
                "answer": OUT_OF_SCOPE_REPLY,
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
    def _looks_like_prompt_injection(question: str) -> bool:
        lowered = question.lower()
        return any(re.search(pattern, lowered) for pattern in UNSAFE_PROMPT_PATTERNS)

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
