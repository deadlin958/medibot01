"""
Configuration — loads environment variables and sets model/path constants.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ── OpenAI ─────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ── Model names ─────────────────────────────────────────────────────────────
GPT_TEXT_MODEL: str = "gpt-4o"
GPT_VISION_MODEL: str = "gpt-4o"        # gpt-4o supports vision natively
LLM_TEMPERATURE: float = 0.2            # factual & conservative

# ── Embedding model (local, free) ───────────────────────────────────────────
EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

# ── Paths ────────────────────────────────────────────────────────────────────
RAW_CSV: Path            = BASE_DIR / "pubmedqa.csv"
SYSTEM_PROMPT_FILE: Path = BASE_DIR / "system prompt.txt"
CLEANED_JSONL: Path      = BASE_DIR / "data" / "cleaned_pubmedqa.jsonl"
CHROMA_DB_DIR: Path      = BASE_DIR / "data" / "chroma_db"

# ── ChromaDB ─────────────────────────────────────────────────────────────────
CHROMA_COLLECTION: str = "pubmedqa"

# ── Chunking ─────────────────────────────────────────────────────────────────
CHUNK_SIZE: int    = 512    # characters (approx 120–140 tokens for MiniLM)
CHUNK_OVERLAP: int = 64

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K_RESULTS: int = 5

# ── Conversation memory ───────────────────────────────────────────────────────
MEMORY_WINDOW_SIZE: int = 10   # last N exchanges kept in context

# ── Frontend static files ────────────────────────────────────────────────────
STATIC_DIR: Path = BASE_DIR / "frontend"

# ── Safety disclaimer (must appear verbatim in every response) ───────────────
DISCLAIMER: str = (
    "Disclaimer: This information is for general guidance only. "
    "Please do not rely on it completely. "
    "Always consult a qualified doctor for proper medical advice."
)

# ── Emergency trigger keywords ─────────────────────────────────────────────
EMERGENCY_KEYWORDS: list[str] = [
    "chest pain", "difficulty breathing", "shortness of breath",
    "stroke", "unconscious", "severe bleeding", "heart attack",
    "can't breathe", "cannot breathe", "crushing chest",
    "sudden numbness", "face drooping", "arm weakness", "speech difficulty",
    "seizure", "overdose", "suicidal", "suicide", "anaphylaxis",
]
