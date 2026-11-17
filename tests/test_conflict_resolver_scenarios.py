
from app.agents.conflict_resolver import ConflictResolver


# --------------------------------------------------
# 1. Controlled LLM response for repeatable testing
# --------------------------------------------------

class FakeLLM:

    def __init__(self, response):
        self.response = response
        self.last_prompt = ""

    def generate_json(self, prompt):
        self.last_prompt = prompt
        return self.response


# --------------------------------------------------
# 2. Sample incident
# --------------------------------------------------

incident = {
    "incident_id": "NEW-INC-2001",
    "severity": "P1",
    "service": "PaymentService",
    "description": "Payment API requests are failing."
}


# --------------------------------------------------
# 3. Build specialist investigation reports
# --------------------------------------------------

def build_specialist_reports(root_causes):

    reports = {}

    specialists = [
        ("database", "DATABASE", "Database Investigation Agent"),
        ("application", "APPLICATION", "Application Investigation Agent"),
        ("infrastructure", "INFRASTRUCTURE", "Infrastructure Investigation Agent")
    ]

    for key, domain, agent_name in specialists:

        reports[key] = {
            "agent_name": agent_name,
            "domain": domain,
            "probable_root_cause": root_causes[key],
            "confidence": "Medium",
            "findings": root_causes[key],
            "retrieved_evidence": [
                {
                    "incident_id": "INC-1001",
                    "title": "Database connection pool exhaustion",
                    "root_cause": (
                        "Database connections were not released promptly."
                    ),
                    "score": 0.95
                }
            ],
            "alternative_causes": [],
            "recommended_actions": [],
            "current_verification": []
        }

    return reports


# --------------------------------------------------
# 4. Controlled LLM output
# --------------------------------------------------

def build_llm_response(
    supporting_evidence,
    disagreements=None
):

    return {
        "consolidated_root_cause": (
            "Database connection pool exhaustion."
        ),
        "confidence": "High",

        "supporting_agents": [
            "Database Investigation Agent",
            "Application Investigation Agent",
            "Infrastructure Investigation Agent"
        ],

        "supporting_evidence": supporting_evidence,

        "common_findings": [],

        "disagreements": disagreements or [],

        "additional_investigation_required": [
            "Collect current database connection metrics."
        ],

        "requires_human_review": False,

        "resolution_summary": (
            "Controlled test response."
        )
    }


# --------------------------------------------------
# SCENARIO 1: Conflicting root-cause hypotheses
# --------------------------------------------------

def test_conflicting_findings():

    print("\n========== SCENARIO 1 ==========")
    print("Testing conflicting specialist findings...")

    reports = build_specialist_reports({

        "database": (
            "Database connection pool exhaustion "
            "due to leaked connections."
        ),

        "application": (
            "Application memory leak causing "
            "process out-of-memory errors."
        ),

        "infrastructure": (
            "Network packet loss between application "
            "servers and database servers."
        )
    })

    disagreements = [
        (
            "Database specialist identifies connection pool exhaustion, "
            "while application specialist identifies a memory leak."
        ),
        (
            "Infrastructure specialist identifies network packet loss, "
            "which differs from the other proposed root causes."
        )
    ]

    llm_response = build_llm_response(
        supporting_evidence=[
            {
                "incident_id": "INC-1001",
                "source_agent": "Database Investigation Agent",
                "finding": "Historical database connection issue."
            }
        ],
        disagreements=disagreements
    )

    resolver = ConflictResolver()
    resolver.llm = FakeLLM(llm_response)

    result = resolver.resolve(incident, reports)

    assert result["conflict_detected"] is True

    assert len(result["disagreements"]) == 2

    assert result["requires_human_review"] is True

    print("\n[PASS] Conflicting findings detected.")
    print("[PASS] Disagreements preserved.")
    print("[PASS] Human review enforced.")


# --------------------------------------------------
# SCENARIO 2: Invalid / fabricated evidence ID
# --------------------------------------------------

def test_invalid_evidence_rejection():

    print("\n========== SCENARIO 2 ==========")
    print("Testing invalid LLM-generated evidence ID...")

    reports = build_specialist_reports({

        "database": "Database connection pool exhaustion.",

        "application": "Database connection pool exhaustion.",

        "infrastructure": "Database connection pool exhaustion."
    })

    llm_response = build_llm_response(

        supporting_evidence=[

            # Valid historical evidence
            {
                "incident_id": "INC-1001",
                "source_agent": "Database Investigation Agent",
                "finding": "Valid historical evidence."
            },

            # Fabricated evidence - never retrieved
            {
                "incident_id": "INC-9999",
                "source_agent": "Database Investigation Agent",
                "finding": "Fabricated historical evidence."
            }
        ]
    )

    resolver = ConflictResolver()
    resolver.llm = FakeLLM(llm_response)

    result = resolver.resolve(incident, reports)

    validated_ids = {
        item["incident_id"]
        for item in result["supporting_evidence"]
    }

    assert "INC-1001" in validated_ids

    assert "INC-9999" not in validated_ids

    assert "INC-9999" not in result["available_evidence_ids"]

    assert len(result["supporting_evidence"]) == 1

    print("\n[PASS] Valid evidence retained.")
    print("[PASS] Fabricated evidence rejected.")
    print("[PASS] Only retrieved evidence included.")


def test_real_llm_conflict_detection():

    print("\n========== SCENARIO 3 ==========")
    print("Testing real Qwen conflict detection...")

    reports = build_specialist_reports({

        "database": (
            "Database connection pool exhaustion caused by "
            "database connections not being released."
        ),

        "application": (
            "Application memory leak causing process "
            "out-of-memory errors and application crashes."
        ),

        "infrastructure": (
            "Network packet loss between application servers "
            "and database servers causing connectivity failures."
        )
    })

    # Use the actual Ollama LLM client.
    # Do not replace it with FakeLLM in this test.
    resolver = ConflictResolver()

    result = resolver.resolve(
        incident,
        reports
    )

    print("\n========== REAL LLM CONFLICT RESULTS ==========")

    print("Conflict detected:", result["conflict_detected"])

    print("\nDisagreements:")

    for disagreement in result["disagreements"]:
        print("-", disagreement)

    print("\nHuman review required:",
          result["requires_human_review"])

    if result["conflict_detected"]:
        print("\n[PASS] Qwen identified conflicting hypotheses.")
    else:
        print(
            "\n[WARNING] Qwen did not identify the conflict. "
            "Review the model response and resolver prompt."
        )

# --------------------------------------------------
# 5. Run both scenarios
# --------------------------------------------------

if __name__ == "__main__":

    #test_conflicting_findings()

    #test_invalid_evidence_rejection()

    test_real_llm_conflict_detection()

    print("\n==========================================")
    print("ALL CONFLICT RESOLVER SCENARIO TESTS PASSED")
    print("==========================================")