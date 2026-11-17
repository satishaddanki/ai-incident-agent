# app/agents/rca_agent.py
import json

from app.core.ollama_client import OllamaLLMClient
from app.rag.retriever import IncidentRetriever


# RCA - Root Cause Analysis Agent
class RootCauseAnalysisAgent:
    """Investigates incidents using retrieved historical evidence."""

    def __init__(self):

        self.retriever = IncidentRetriever()
        self.llm = OllamaLLMClient()

    def investigate(self, incident: dict):

        # Step 1: Retrieve relevant historical incidents
        query = (
            f"Incident: {incident['description']}\n"
            f"Service: {incident['service']}\n"
            f"Logs: {incident.get('logs', 'Not provided')}"
        )

        evidence = self.retriever.search(
            query=query,
            top_k=3
        )

        # Step 2: Prepare evidence for the LLM
        evidence_text = json.dumps(
            evidence,
            indent=2
        )

        # Step 3: Build investigation prompt
        prompt = f"""
You are an experienced Site Reliability Engineer
and production incident investigation specialist.

Your responsibility is to investigate the supplied
production incident using only the available evidence.

CURRENT INCIDENT:
{json.dumps(incident, indent=2)}

RETRIEVED HISTORICAL EVIDENCE:
{evidence_text}

INSTRUCTIONS:

1. Identify the most likely root cause.
2. Compare the current symptoms with historical incidents.
3. Cite historical incident IDs supporting your analysis.
4. Distinguish confirmed facts from hypotheses.
5. Never invent logs, metrics or technical evidence.
6. If evidence is insufficient, explicitly say so.
7. Recommend corrective and preventive actions.
8. Identify additional information needed for validation.
9. Assign confidence as Low, Medium or High.
10. Confidence must reflect the strength of available evidence,
    not simply the similarity scores.

Return valid JSON using exactly this structure:

{{
  "incident_summary": "string",
  "probable_root_cause": "string",
  "supporting_evidence": [
    {{
      "incident_id": "string",
      "explanation": "string"
    }}
  ],
  "confidence": "Low, Medium or High",
  "reasoning": "string",
  "recommended_actions": [
    "string"
  ],
  "missing_information": [
    "string"
  ],
  "requires_human_investigation": true
}}
"""

        # Step 4: Generate RCA report
        report = self.llm.generate_json(prompt)

        # Attach retrieval evidence for traceability
        report["retrieved_incidents"] = evidence

        return report


if __name__ == "__main__":

    agent = RootCauseAnalysisAgent()

    sample_incident = {
        "incident_id": "NEW-INC-2001",
        "severity": "P1",
        "service": "PaymentService",
        "description": (
            "Payment API requests are failing during peak traffic. "
            "Users are experiencing database connection timeouts. "
            "The connection pool appears to be exhausted."
        ),
        "logs": (
            "Timeout waiting for an available database connection. "
            "Connection pool maximum limit reached."
        )
    }

    print("Starting Root Cause Investigation...\n")

    report = agent.investigate(sample_incident)

    print("========== RCA INVESTIGATION REPORT ==========\n")

    print(
        json.dumps(
            report,
            indent=2
        )
    )
