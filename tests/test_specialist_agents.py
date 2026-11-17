# test_specialist_agents.py

import json

from app.agents.specialist_agents import (
    DatabaseInvestigationAgent,
    ApplicationInvestigationAgent,
    InfrastructureInvestigationAgent
)


incident = {
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


agents = [
    DatabaseInvestigationAgent(),
    ApplicationInvestigationAgent(),
    InfrastructureInvestigationAgent()
]


print("\n========== SPECIALIST AGENT TEST ==========\n")

results = []

for agent in agents:

    expected_name = agent.agent_name
    expected_domain = agent.domain

    result = agent.investigate(incident)

    # Validate agent identity
    assert result["agent_name"] == expected_name, (
        f"Identity mismatch: expected {expected_name}, "
        f"received {result['agent_name']}"
    )

    # Validate domain
    assert result["domain"] == expected_domain

    # Validate incident ID
    assert result["incident_id"] == incident["incident_id"]

    results.append(result)

    print("\n========== INVESTIGATION RESULT ==========\n")

    print(json.dumps(result, indent=2))


print("\n========== VALIDATION SUMMARY ==========\n")

for result in results:

    print(
        f"{result['agent_name']} | "
        f"{result['domain']} | "
        f"Confidence: {result['confidence']} | "
        f"Unique Evidence: {result['unique_evidence_count']}"
    )

print("\nAll specialist identity validations PASSED.")
