#  app/agents/specialist_agents.py
import json

from app.core.ollama_client import (
    OllamaEmbeddingClient,
    OllamaLLMClient
)
from app.rag.retriever import IncidentRetriever


class SpecialistInvestigationAgent:
    """
    Base class for specialized incident investigation agents.
    Each specialist investigates a specific technical domain.
    """

    def __init__(self, agent_name, domain, investigation_scope):

        self.agent_name = agent_name
        self.domain = domain
        self.investigation_scope = investigation_scope

        self.llm = OllamaLLMClient()
        self.retriever = IncidentRetriever()

    def _deduplicate_evidence(self, evidence):
        """
        Keep only one record per historical incident.
        Preserve the record with the highest retrieval score.
        """

        unique_evidence = {}

        for item in evidence:

            incident_id = item.get("incident_id")

            if not incident_id:
                continue

            existing = unique_evidence.get(incident_id)

            if existing is None:
                unique_evidence[incident_id] = item

            else:
                current_score = item.get("score", 0)
                existing_score = existing.get("score", 0)

                if current_score > existing_score:
                    unique_evidence[incident_id] = item

        return sorted(
            unique_evidence.values(),
            key=lambda item: item.get("score", 0),
            reverse=True
        )

    def investigate(self, incident):

        print(
            f"\n[{self.agent_name}] "
            f"Investigation started. Domain={self.domain}"
        )

        # 1. Build domain-specific retrieval query
        query = f"""
        Domain: {self.domain}
        Service: {incident.get('service')}
        Incident: {incident.get('description')}
        Logs: {incident.get('logs', 'Not provided')}
        Investigation scope: {self.investigation_scope}
        """

        # 2. Retrieve historical evidence
        raw_evidence = self.retriever.search(
            query=query,
            top_k=3
        )

        # 3. Deduplicate historical evidence
        evidence = self._deduplicate_evidence(raw_evidence)

        print(
            f"[{self.agent_name}] "
            f"Retrieved {len(raw_evidence)} chunks; "
            f"{len(evidence)} unique historical incidents."
        )

        # 4. Build specialist investigation prompt
        prompt = f"""
You are {self.agent_name}, an enterprise
Site Reliability Engineering specialist.

Your assigned domain is: {self.domain}

INVESTIGATION SCOPE:
{self.investigation_scope}

CURRENT INCIDENT:
{json.dumps(incident, indent=2)}

RETRIEVED HISTORICAL EVIDENCE:
{json.dumps(evidence, indent=2)}

IMPORTANT EVIDENCE RULES:

1. Investigate only your assigned technical domain.
2. Historical incidents are reference material,
   not proof of the current incident's root cause.
3. Do not claim that historical metrics or logs
   are current incident measurements.
4. Clearly distinguish observed facts,
   historical evidence and hypotheses.
5. Cite only incident IDs present in retrieved evidence.
6. Do not invent logs, metrics or infrastructure details.
7. Do not assume that missing infrastructure evidence
   confirms an infrastructure problem.
8. If current evidence is insufficient, say so.
9. Identify alternative possible causes.
10. Recommend diagnostic checks within your domain.
11. Do not execute remediation actions.
12. Assign confidence based on available evidence.

CONFIDENCE GUIDANCE:

High:
Direct and sufficient current-incident evidence.

Medium:
Some relevant evidence, but further validation is needed.

Low:
Insufficient evidence or mainly unverified hypotheses.

Return valid JSON using this structure:

{{
    "findings": "Investigation findings",
    "probable_root_cause": "Potential root cause or insufficient evidence",
    "supporting_evidence": [
        {{
            "incident_id": "Historical incident ID",
            "explanation": "Evidence explanation"
        }}
    ],
    "confidence": "Low/Medium/High",
    "reasoning": "Reason for confidence",
    "alternative_causes": [],
    "recommended_actions": [],
    "missing_information": [],
    "investigation_status": "COMPLETED"
}}
"""

        # 5. Invoke LLM
        result = self.llm.generate_json(prompt)

        # 6. Validate LLM response
        if not isinstance(result, dict):
            raise ValueError(
                f"{self.agent_name} returned invalid JSON structure."
            )

        allowed_confidence = {"Low", "Medium", "High"}

        confidence = result.get("confidence")

        if confidence not in allowed_confidence:
            result["confidence"] = "Low"

        # 7. Validate supporting evidence references
        valid_incident_ids = {
            item["incident_id"] for item in evidence
        }

        validated_supporting_evidence = []

        for item in result.get("supporting_evidence", []):

            if (
                isinstance(item, dict)
                and item.get("incident_id") in valid_incident_ids
            ):
                validated_supporting_evidence.append(item)

        result["supporting_evidence"] = (
            validated_supporting_evidence
        )

        # 8. Enforce application-controlled identity
        result["agent_name"] = self.agent_name
        result["domain"] = self.domain
        result["incident_id"] = incident["incident_id"]

        # 9. Attach authoritative retrieval results
        result["retrieved_evidence"] = evidence
        result["retrieval_chunk_count"] = len(raw_evidence)
        result["unique_evidence_count"] = len(evidence)

        # 10. Enforce investigation status
        result["investigation_status"] = "COMPLETED"

        print(
            f"[{self.agent_name}] "
            f"Investigation completed. "
            f"Confidence={result['confidence']}"
        )

        return result


class DatabaseInvestigationAgent(SpecialistInvestigationAgent):

    def __init__(self):

        super().__init__(
            agent_name="Database Investigation Agent",
            domain="DATABASE",
            investigation_scope="""
            Investigate:
            - Database connection pool exhaustion
            - Connection timeout errors
            - Long-running SQL queries
            - Database locks and deadlocks
            - Database CPU and memory pressure
            - Connection leaks
            - Active versus idle connections
            - Query execution plans
            """
        )


class ApplicationInvestigationAgent(SpecialistInvestigationAgent):

    def __init__(self):

        super().__init__(
            agent_name="Application Investigation Agent",
            domain="APPLICATION",
            investigation_scope="""
            Investigate:
            - Application exceptions
            - API request failures
            - Thread pool exhaustion
            - Connection management in application code
            - Application memory and CPU usage
            - Slow application requests
            - Retry and timeout configuration
            - Request concurrency and connection disposal
            """
        )


class InfrastructureInvestigationAgent(SpecialistInvestigationAgent):

    def __init__(self):

        super().__init__(
            agent_name="Infrastructure Investigation Agent",
            domain="INFRASTRUCTURE",
            investigation_scope="""
            Investigate:
            - Server resource exhaustion
            - Network connectivity problems
            - DNS resolution failures
            - Container resource limits
            - Kubernetes pod restarts
            - Infrastructure capacity constraints
            - Load balancer and network issues
            - Network latency and packet loss
            """
        )
