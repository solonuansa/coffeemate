import logging
import re
from typing import Any, Dict, List

from backend.config.settings import SCORE_THRESHOLD
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
NEED_MORE_DETAIL_REPLY = (
    "Pertanyaanmu masih terlalu umum. Aku bisa bantu lebih tepat kalau kamu tambahkan "
    "detail seperti area (mis. Sleman/Kota Jogja), kebutuhan (WFC/meeting/nongkrong), "
    "atau preferensi suasana."
)
COFFEE_DOMAIN_KEYWORDS = [
    "kopi",
    "coffee",
    "coffeeshop",
    "cafe",
    "ngopi",
    "wfc",
    "nongkrong",
    "espresso",
    "latte",
    "cappuccino",
    "manual brew",
    "v60",
    "yogyakarta",
    "jogja",
    "sleman",
    "bantul",
    "kulon progo",
    "gunungkidul",
]
GENERIC_FOLLOW_UP_SUGGESTIONS = [
    "Rekomendasikan coffee shop untuk WFC di Sleman",
    "Rekomendasikan coffee shop yang tenang untuk meeting di Kota Jogja",
    "Rekomendasikan coffee shop di Jogja dengan kopi susu yang enak",
]


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
                "fallback_type": "out_of_scope",
            }

        adaptive_threshold = self._adaptive_threshold(question)
        documents, _rejected_documents = self.retriever.retrieve_with_threshold_diagnostics(
            question,
            threshold=adaptive_threshold,
        )
        if not documents:
            is_domain_query = self._is_coffee_domain_query(question)
            return {
                "answer": NEED_MORE_DETAIL_REPLY if is_domain_query else OUT_OF_SCOPE_REPLY,
                "sources": [],
                "follow_up_suggestions": (
                    GENERIC_FOLLOW_UP_SUGGESTIONS if is_domain_query else []
                ),
                "fallback_type": "too_generic" if is_domain_query else "out_of_scope",
            }

        context = self.retriever.format_context(documents)
        answer = self.generator.generate(question, context)
        sources = self._extract_sources(documents)

        return {
            "answer": answer,
            "sources": sources,
            "follow_up_suggestions": [],
            "fallback_type": None,
        }

    @staticmethod
    def _looks_like_prompt_injection(question: str) -> bool:
        lowered = question.lower()
        return any(re.search(pattern, lowered) for pattern in UNSAFE_PROMPT_PATTERNS)

    @staticmethod
    def _is_coffee_domain_query(question: str) -> bool:
        lowered = question.lower()
        return any(keyword in lowered for keyword in COFFEE_DOMAIN_KEYWORDS)

    @staticmethod
    def _adaptive_threshold(question: str) -> float:
        word_count = len(question.split())
        if word_count <= 3:
            return min(0.55, SCORE_THRESHOLD + 0.25)
        if word_count <= 6:
            return min(0.45, SCORE_THRESHOLD + 0.15)
        if word_count <= 10:
            return min(0.35, SCORE_THRESHOLD + 0.05)
        return SCORE_THRESHOLD

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
