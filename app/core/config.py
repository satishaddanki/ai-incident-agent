# app/core/config.py
import os
from pathlib import Path

from dotenv import load_dotenv


# Resolve the project root:
# app/core/config.py -> app/core -> app -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

# Load environment variables from the project root .env
load_dotenv(dotenv_path=ENV_FILE)


# Qdrant Configuration
QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://localhost:6333"
)

# Qdrant Collection Name Configuration
QDRANT_COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION_NAME",
    "incident_knowledge"
)


# RAG Chunking Configuration
RAG_CHUNK_SIZE = int(
    os.getenv("RAG_CHUNK_SIZE", "350")
)

# RAG Chunk Overlap Configuration
RAG_CHUNK_OVERLAP = int(
    os.getenv("RAG_CHUNK_OVERLAP", "60")
)

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

# Ollama Model Configuration
OLLAMA_LLM_MODEL = os.getenv(
    "OLLAMA_LLM_MODEL",
    "qwen2.5:7b"
)

# Ollama Embedding Model Configuration
OLLAMA_EMBEDDING_MODEL = os.getenv(
    "OLLAMA_EMBEDDING_MODEL",
    "nomic-embed-text:latest"
)

# Vector Configuration
VECTOR_SIZE = int(
    os.getenv("VECTOR_SIZE", "768")
)

# Incident dataset configuration
INCIDENT_DATA_FILE = Path(
    os.getenv(
        "INCIDENT_DATA_FILE",
        "data/incidents/incidents.json"
    )
)

# Resolve relative dataset paths from project root
if not INCIDENT_DATA_FILE.is_absolute():
    INCIDENT_DATA_FILE = PROJECT_ROOT / INCIDENT_DATA_FILE

# Configuration validation
if not QDRANT_URL:
    raise ValueError("QDRANT_URL cannot be empty.")

if not QDRANT_COLLECTION_NAME:
    raise ValueError("QDRANT_COLLECTION_NAME cannot be empty.")

if RAG_CHUNK_SIZE <= 0:
    raise ValueError("RAG_CHUNK_SIZE must be greater than zero.")

if RAG_CHUNK_OVERLAP < 0:
    raise ValueError("RAG_CHUNK_OVERLAP cannot be negative.")

if RAG_CHUNK_OVERLAP >= RAG_CHUNK_SIZE:
    raise ValueError(
        "RAG_CHUNK_OVERLAP must be smaller than RAG_CHUNK_SIZE."
    )
if VECTOR_SIZE <= 0:
    raise ValueError("VECTOR_SIZE must be greater than zero.")

if not INCIDENT_DATA_FILE.exists():
    raise FileNotFoundError(
        f"Incident dataset not found: {INCIDENT_DATA_FILE}"
    )