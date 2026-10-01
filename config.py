import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def _endpoint() -> str:
    """Accepts the resource URL with or without /openai/v1 and returns the v1 base URL."""
    raw = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
    if raw.endswith("/openai/v1"):
        raw = raw[: -len("/openai/v1")]
    return f"{raw}/openai/v1/"


AZURE_BASE_URL = _endpoint()
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
CHAT_DEPLOYMENT = os.getenv(
    "CHAT_DEPLOYMENT", os.getenv("AZURE_LLM_DEPLOYMENT", "gpt-6-luna")
)
EMBEDDING_DEPLOYMENT = os.getenv(
    "EMBEDDING_DEPLOYMENT",
    os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
)
EMBEDDING_DIM = 1536  # text-embedding-3-small

_uri = os.getenv("MILVUS_DB_PATH", os.getenv("MILVUS_URI", "./data/milvus_lite.db"))
MILVUS_URI = (
    str((ROOT / _uri).resolve())
    if _uri.endswith(".db") and not os.path.isabs(_uri)
    else _uri
)
MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "support_kb")
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.25"))
KB_PATH = ROOT / "data" / "kb.json"


def require_key() -> None:
    if not AZURE_API_KEY:
        raise RuntimeError("AZURE_OPENAI_API_KEY is empty. Set it in chatbot/.env")