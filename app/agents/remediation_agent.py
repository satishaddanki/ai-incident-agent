# app/agents/remediation_agent.py
import json

from app.core.ollama_client import OllamaLLMClient
from app.agents.rca_agent import RootCauseAnalysisAgent

class RemediationAgent:
    """
    Creates safe remediation plans using RCA findings.
    Does not execute production changes.
    """

    def __init__(self):
        self.llm = OllamaLLMClient()

    def generate_plan(self, rca_report: dict):

        if not rca_report.get("probable_root_cause"):
            raise ValueError("RCA root cause is missing.")

        # Prepare RCA findings for remediation planning
        rca_context = {
            "incident_summary": rca_report.get(
                "incident_summary"
            ),
            "probable_root_cause": rca_report.get(
                "probable_root_cause"
            ),
            "supporting_evidence": rca_report.get(
                "supporting_evidence", []
            ),
            "confidence": rca_report.get("confidence"),
            "recommended_actions": rca_report.get(
                "recommended_actions", []
            ),
            "missing_information": rca_report.get(
                "missing_information", []
            )
        }

        prompt = f"""
You are an experienced Site Reliability Engineer
and Production Remediation Specialist.

Your task is to prepare a safe remediation plan
based on the supplied Root Cause Analysis report.

RCA REPORT:
{json.dumps(rca_context, indent=2)}

REQUIREMENTS:

1. Create actionable remediation steps.
2. Prioritize actions as Critical, High, Medium or Low.
3. Explain the expected outcome of every action.
4. Identify the risk associated with each action.
5. Include validation steps.
6. Include rollback instructions where applicable.
7. Separate immediate mitigation from permanent fixes.
8. Do not invent infrastructure details.
9. Do not assume production access or permissions.
10. Do not execute any action.
11. Require explicit human approval before execution.
12. If evidence is insufficient, recommend investigation
    before making risky production changes.

Return valid JSON in this structure:

{{
  "incident_id": "string",
  "remediation_summary": "string",
  "immediate_mitigation": [
    {{
      "action": "string",
      "priority": "Critical/High/Medium/Low",
      "expected_outcome": "string",
      "risk": "string"
    }}
  ],
  "permanent_fixes": [
    {{
      "action": "string",
      "priority": "Critical/High/Medium/Low",
      "expected_outcome": "string",
      "risk": "string"
    }}
  ],
  "validation_steps": [
    "string"
  ],
  "rollback_plan": [
    "string"
  ],
  "requires_human_approval": true
}}
"""

        plan = self.llm.generate_json(prompt)

        # Enforce safety controls in application code,
        # rather than trusting the LLM to enforce them.
        plan["requires_human_approval"] = True
        plan["execution_status"] = "NOT_EXECUTED"

        return plan


if __name__ == "__main__":

    print("Starting Incident Investigation Workflow...\n")

    # Step 1: Investigate the incident
    rca_agent = RootCauseAnalysisAgent()

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

    rca_report = rca_agent.investigate(sample_incident)

    print("RCA investigation completed.")

    # Step 2: Generate remediation plan
    remediation_agent = RemediationAgent()

    remediation_plan = remediation_agent.generate_plan(
        rca_report
    )

    print("\n========== REMEDIATION PLAN ==========\n")

    print(
        json.dumps(
            remediation_plan,
            indent=2
        )
    )
