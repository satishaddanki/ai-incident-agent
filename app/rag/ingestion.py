# app/rag/ingestion.py
import json
import uuid
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

from app.core.config import (
    QDRANT_URL,
    QDRANT_COLLECTION_NAME,
    VECTOR_SIZE,
    RAG_CHUNK_SIZE,
    RAG_CHUNK_OVERLAP,
    INCIDENT_DATA_FILE,
)

from app.core.ollama_client import OllamaEmbeddingClient


# Configuration
COLLECTION_NAME = QDRANT_COLLECTION_NAME

DATA_FILE = INCIDENT_DATA_FILE

CHUNK_SIZE = RAG_CHUNK_SIZE
CHUNK_OVERLAP = RAG_CHUNK_OVERLAP


def load_incidents():
    """Load incident records from JSON."""

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def chunk_text(text, chunk_size=CHUNK_SIZE,
               overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks."""

    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size.")

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def create_collection(client):
    """Create the Qdrant collection if it doesn't exist."""

    if not client.collection_exists(COLLECTION_NAME):

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )

        print(f"Created collection: {COLLECTION_NAME}")

    else:
        print(f"Collection already exists: {COLLECTION_NAME}")


def ingest_incidents():

    print("Starting incident ingestion...")

    # Initialize clients
    qdrant = QdrantClient(url=QDRANT_URL)

    embedding_client = OllamaEmbeddingClient()

    # Load records
    incidents = load_incidents()

    print(f"Loaded {len(incidents)} incident records.")

    # Create vector collection
    create_collection(qdrant)

    points = []

    for incident in incidents:

        # Build searchable document text
        document_text = (
            f"Incident: {incident['title']}\n"
            f"Description: {incident['description']}\n"
            f"Root Cause: {incident['root_cause']}\n"
            f"Remediation: {incident['remediation']}\n"
            f"Service: {incident['service']}\n"
            f"Severity: {incident['severity']}"
        )

        # Split document into chunks
        chunks = chunk_text(document_text)

        print(
            f"{incident['incident_id']}: "
            f"{len(chunks)} chunks"
        )

        for index, chunk in enumerate(chunks):

            # Generate embedding
            vector = embedding_client.generate_embedding(chunk)

            # Stable ID prevents duplicate points on reruns
            point_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{incident['incident_id']}:{index}"
                )
            )

            # Prepare Qdrant point
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "incident_id": incident["incident_id"],
                    "severity": incident["severity"],
                    "service": incident["service"],
                    "title": incident["title"],
                    "root_cause": incident["root_cause"],
                    "remediation": incident["remediation"],
                    "tags": incident["tags"],
                    "chunk_index": index,
                    "text": chunk
                }
            )

            points.append(point)

    # Insert vectors into Qdrant
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=True
    )

    # Verify stored points
    collection_info = qdrant.get_collection(
        COLLECTION_NAME
    )

    print("\nIngestion completed successfully.")
    print(f"Total vectors submitted: {len(points)}")
    print(
        "Vectors stored:",
        collection_info.points_count
    )


if __name__ == "__main__":
    ingest_incidents()
