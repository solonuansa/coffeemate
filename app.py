import os
from dotenv import load_dotenv
load_dotenv() 

import sys
import logging
from src.rag_service import RAGService

import warnings


warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.ERROR)

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RAGApp:
    """Aplikasi RAG Sederhana"""
    
    def __init__(self):
        """Inisialisasi aplikasi RAG"""
        print("=" * 60)
        print("Sistem RAG Coffee Shop")
        print()
        
        self.rag_service = RAGService()
        
        print()
    
    def query(self, question: str) -> dict:
        """
        Query ke sistem RAG
        
        Args:
            question: Pertanyaan dari user
            
        Returns:
            Dictionary dengan jawaban dan sumber
        """
        print(f"Query: {question}")
        print("-" * 60)
        return self.rag_service.ask(question)
    
    def print_response(self, response: dict):
        """
        Print response dalam format yang rapi
        
        Args:
            response: Dictionary response dari query()
        """
        print()
        print("Jawaban:")
        print("=" * 60)
        print(response["answer"])
        print()
        
        if response["sources"]:
            print("Sumber informasi:")
            print("-" * 60)
            for i, source in enumerate(response["sources"], 1):
                print(f"{i}. {source['nama']} - {source['lokasi']}")
        print()


def main():
    """Fungsi utama - Mode interaktif"""
    
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY tidak ditemukan!")
        print("Silakan set Groq API key Anda:")
        print("  export GROQ_API_KEY='your_api_key_here'  # Linux/Mac")
        print("  set GROQ_API_KEY=your_api_key_here       # Windows CMD")
        print("  $env:GROQ_API_KEY='your_api_key_here'    # Windows PowerShell")
        print()
        print("Dapatkan API key dari: https://console.groq.com/")
        sys.exit(1)

    try:
        app = RAGApp()
    except FileNotFoundError as e:
        logger.error(f"Error saat inisialisasi: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error tak terduga saat inisialisasi: {e}", exc_info=True)
        print(f"Error tak terduga: {e}")
        sys.exit(1)

    print("=" * 60)
    print("Ketik pertanyaan tentang coffee shop")
    print("Ketik 'exit' atau 'quit' untuk keluar")
    print("=" * 60)
    print()

    while True:
        try:
            question = input(">> ").strip()
            
            if question.lower() in ["exit", "quit"]:
                break

            if not question:
                continue
            
            # Input sanitization
            if len(question) > 500:
                print("Pertanyaan terlalu panjang. Maksimal 500 karakter.")
                continue
            
            response = app.query(question)
            app.print_response(response)
            
        except KeyboardInterrupt:
            print("\n\nSampai jumpa")
            break
        except Exception as e:
            logger.error(f"Error saat memproses query: {e}", exc_info=True)
            print(f"Error: {e}")
            print("Silakan coba lagi.")


if __name__ == "__main__":
    main()
