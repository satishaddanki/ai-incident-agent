# app/rag/retriever.py
from qdrant_client import QdrantClient

from app.core.ollama_client import OllamaEmbeddingClient

from app.core.config import (
    QDRANT_URL,
    QDRANT_COLLECTION_NAME,
)

QDRANT_URL = QDRANT_URL
COLLECTION_NAME = QDRANT_COLLECTION_NAME


class IncidentRetriever:

    def __init__(self):

        self.qdrant = QdrantClient(url=QDRANT_URL)

        self.embedding_client = OllamaEmbeddingClient()

    def search(self, query: str, top_k: int = 3):

        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        # Step 1: Convert user query into an embedding
        query_vector = (
            self.embedding_client.generate_embedding(query)
        )

        # Step 2: Search Qdrant
        search_result = self.qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
            with_payload=True
        )

        # Step 3: Return relevant incidents
        results = []

        for point in search_result.points:

            results.append({
                "score": point.score,
                "incident_id": point.payload.get("incident_id"),
                "severity": point.payload.get("severity"),
                "service": point.payload.get("service"),
                "title": point.payload.get("title"),
                "root_cause": point.payload.get("root_cause"),
                "remediation": point.payload.get("remediation"),
                "text": point.payload.get("text")
            })

        return results


if __name__ == "__main__":

    retriever = IncidentRetriever()

    query = (
        "Payment API is failing because database "
        "connections are exhausted. Find similar "
        "historical incidents and recommend corrective actions."
    )

    results = retriever.search(query, top_k=3)

    print("\n========== INCIDENT SEARCH RESULTS ==========\n")

    for index, incident in enumerate(results, start=1):

        print(f"Result: {index}")
        print(f"Incident ID: {incident['incident_id']}")
        print(f"Similarity Score: {incident['score']:.4f}")
        print(f"Severity: {incident['severity']}")
        print(f"Service: {incident['service']}")
        print(f"Title: {incident['title']}")
        print(f"Root Cause: {incident['root_cause']}")
        print(f"Remediation: {incident['remediation']}")
        print("-" * 60)
