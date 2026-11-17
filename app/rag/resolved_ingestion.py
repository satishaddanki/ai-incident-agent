# app/rag/resolved_ingestion.py
import hashlib
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from app.core.ollama_client import OllamaEmbeddingClient

from app.core.config import (
    QDRANT_URL,
    QDRANT_COLLECTION_NAME,
    RAG_CHUNK_SIZE,
    RAG_CHUNK_OVERLAP,
)
QDRANT_URL = QDRANT_URL
COLLECTION_NAME = QDRANT_COLLECTION_NAME

CHUNK_SIZE = RAG_CHUNK_SIZE
CHUNK_OVERLAP = RAG_CHUNK_OVERLAP


class ResolvedIncidentIngestor:
    """
    Ingest only successfully executed and independently
    verified incidents into the existing Qdrant collection.
    """

    def __init__(
        self,
        qdrant_client=None,
        embedding_client=None,
    ):
        self.qdrant = qdrant_client or QdrantClient(
            url=QDRANT_URL
        )

        self.embedding_client = (
            embedding_client or OllamaEmbeddingClient()
        )

    def validate_eligibility(self, record: dict) -> None:
        """Reject incidents that are not fully verified."""

        recommendation = record.get(
            "recommendation_record", {}
        )

        action_result = record.get("action_result", {})
        verification = record.get(
            "action_verification", {}
        )
        rca = record.get("rca_report", {})

        checks = {
            "Recommendation not approved":
                recommendation.get("status") == "APPROVED",

            "Corrective action not successfully executed":
                record.get("execution_status") == "VERIFIED_SUCCESS"
                and action_result.get("status") == "SUCCEEDED",

            "Action verification unsuccessful":
                verification.get("status") == "SUCCEEDED",

            "Root cause not independently verified":
                rca.get("current_root_cause_verified") is True,

            "RCA status is not VERIFIED":
                rca.get("root_cause_status") == "VERIFIED",
        }

        failures = [
            message
            for message, passed in checks.items()
            if not passed
        ]

        if failures:
            raise ValueError(
                "Incident is not eligible for RAG ingestion: "
                + "; ".join(failures)
            )

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP,
    ) -> list[str]:

        if overlap >= chunk_size:
            raise ValueError(
                "Overlap must be smaller than chunk size."
            )

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

    def ingest(self, record: dict) -> dict:
        """
        Validate, embed and upsert a verified incident.

        The existing collection is reused.
        """

        self.validate_eligibility(record)

        incident = record["incident"]
        rca = record["rca_report"]

        incident_id = incident["incident_id"]

        if not self.qdrant.collection_exists(
            COLLECTION_NAME
        ):
            raise RuntimeError(
                f"Qdrant collection '{COLLECTION_NAME}' "
                "does not exist. Existing collection "
                "must be preserved."
            )

        document_text = (
            f"Incident: {incident.get('title', incident_id)}\n"
            f"Description: {incident.get('description', '')}\n"
            f"Service: {incident.get('service', '')}\n"
            f"Severity: {incident.get('severity', '')}\n"
            f"Verified Root Cause: {rca.get('probable_root_cause', '')}\n"
            f"Root Cause Status: {rca.get('root_cause_status')}\n"
            f"Reasoning: {rca.get('reasoning', '')}\n"
            f"Supporting Evidence: {rca.get('supporting_evidence', [])}\n"
            f"Remediation: {record.get('remediation_plan', {})}\n"
            f"Execution Status: {record.get('execution_status')}\n"
            f"Verification: {record.get('action_verification', {})}"
        )

        chunks = self.chunk_text(document_text)

        points = []

        for index, chunk in enumerate(chunks):

            vector = (
                self.embedding_client.generate_embedding(chunk)
            )

            # Content-aware stable ID.
            content_hash = hashlib.sha256(
                chunk.encode("utf-8")
            ).hexdigest()

            point_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"resolved:{incident_id}:{index}:{content_hash}"
                )
            )

            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "incident_id": incident_id,
                        "severity": incident.get("severity"),
                        "service": incident.get("service"),
                        "title": incident.get(
                            "title", incident_id
                        ),
                        "root_cause": rca.get(
                            "probable_root_cause"
                        ),
                        "root_cause_status": "VERIFIED",
                        "remediation": str(
                            record.get("remediation_plan", {})
                        ),
                        "chunk_index": index,
                        "source": "verified_resolved_incident",
                        "text": chunk,
                    },
                )
            )

        self.qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
            wait=True,
        )

        return {
            "incident_id": incident_id,
            "status": "INGESTED",
            "vectors_submitted": len(points),
            "collection": COLLECTION_NAME,
        }