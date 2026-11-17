#  tests/test_conflict_resolver.py
from app.workflows.parallel_workflow import build_parallel_workflow
from app.agents.conflict_resolver import ConflictResolver


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


if __name__ == "__main__":

    print("\n========== RUNNING SPECIALIST INVESTIGATIONS ==========\n")

    workflow = build_parallel_workflow()

    parallel_result = workflow.invoke({
        "incident": incident
    })

    investigation_results = parallel_result[
        "investigation_results"
    ]

    resolver = ConflictResolver()

    consolidated_rca = resolver.resolve(
        incident,
        investigation_results
    )

    print("\n========== CONSOLIDATED ROOT CAUSE ANALYSIS ==========\n")

    print(
        __import__("json").dumps(
            consolidated_rca,
            indent=4,
            default=str
        )
    )