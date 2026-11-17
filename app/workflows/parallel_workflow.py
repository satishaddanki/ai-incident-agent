# app/workflows/parallel_workflow.py
from typing import TypedDict, Any
from time import perf_counter

from langgraph.graph import StateGraph, START, END

from app.agents.specialist_agents import (
    DatabaseInvestigationAgent,
    ApplicationInvestigationAgent,
    InfrastructureInvestigationAgent
)

from app.core.logging_config import get_logger
logger = get_logger(__name__)

# ------------------------------------------------
# 1. Shared workflow state
# ------------------------------------------------

class IncidentInvestigationState(TypedDict, total=False):

    incident: dict

    database_result: dict
    application_result: dict
    infrastructure_result: dict

    investigation_results: dict

    total_execution_time: float


# ------------------------------------------------
# 2. Initialize specialist agents
# ------------------------------------------------

database_agent = DatabaseInvestigationAgent()

application_agent = ApplicationInvestigationAgent()

infrastructure_agent = InfrastructureInvestigationAgent()


# ------------------------------------------------
# 3. Supervisor node
# ------------------------------------------------

def supervisor_node(state: IncidentInvestigationState):
    logger.info("Supervisor node initialized | incident_id=%s", state["incident"]["incident_id"])   
    incident = state["incident"]

    print("\n========== SUPERVISOR AGENT ==========\n")

    print(
        f"[Supervisor] Received incident: "
        f"{incident['incident_id']}"
    )

    print("[Supervisor] Severity:", incident["severity"])

    print("[Supervisor] Service:", incident["service"])

    print("[Supervisor] Delegating investigation to specialists.")

    return {}


# ------------------------------------------------
# 4. Database investigation node
# ------------------------------------------------

def database_node(state: IncidentInvestigationState):

    start = perf_counter()

    print("\n[Supervisor] Dispatching Database Agent...")
    logger.info("Dispatching Database Agent | incident_id=%s", state["incident"]["incident_id"])    
    try:
        result = database_agent.investigate(
            state["incident"]
        )
    except Exception as e:
        logger.exception("Database investigation failed | incident_id=%s", state["incident"]["incident_id"])
        raise

    if result["agent_name"] != "Database Investigation Agent":
        raise ValueError("Database agent identity validation failed.")

    elapsed = perf_counter() - start

    result["execution_time_seconds"] = round(elapsed, 2)

    print(
        f"[Database Node] Completed in {elapsed:.2f} seconds."
    )

    return {
        "database_result": result
    }


# ------------------------------------------------
# 5. Application investigation node
# ------------------------------------------------

def application_node(state: IncidentInvestigationState):

    start = perf_counter()

    logger.info("Dispatching Application Agent | incident_id=%s", state["incident"]["incident_id"])
    try:
        result = application_agent.investigate(
            state["incident"]
        )
    except Exception as e:
        logger.exception("Application investigation failed | incident_id=%s", state["incident"]["incident_id"])
        raise

    if result["agent_name"] != "Application Investigation Agent":
        raise ValueError("Application agent identity validation failed.")

    elapsed = perf_counter() - start

    result["execution_time_seconds"] = round(elapsed, 2)

    print(
        f"[Application Node] Completed in {elapsed:.2f} seconds."
    )

    return {
        "application_result": result
    }


# ------------------------------------------------
# 6. Infrastructure investigation node
# ------------------------------------------------

def infrastructure_node(state: IncidentInvestigationState):

    start = perf_counter()

    print("\n[Supervisor] Dispatching Infrastructure Agent...")
    logger.info("Dispatching Infrastructure Agent | incident_id=%s", state["incident"]["incident_id"])
    try:
        result = infrastructure_agent.investigate(
            state["incident"]
        )
    except Exception as e:
        logger.exception("Infrastructure investigation failed | incident_id=%s", state["incident"]["incident_id"])
        raise

    if result["agent_name"] != "Infrastructure Investigation Agent":
        raise ValueError("Infrastructure agent identity validation failed.")

    elapsed = perf_counter() - start

    result["execution_time_seconds"] = round(elapsed, 2)

    print(
        f"[Infrastructure Node] Completed in {elapsed:.2f} seconds."
    )

    return {
        "infrastructure_result": result
    }


# ------------------------------------------------
# 7. Fan-in: Collect all investigation results
# ------------------------------------------------

def collect_results_node(state: IncidentInvestigationState):

    logger.info("Collecting investigation results | incident_id=%s", state["incident"]["incident_id"])
    try:
        results = {
            "database": state["database_result"],
            "application": state["application_result"],
            "infrastructure": state["infrastructure_result"]
        }
    except KeyError as e:
        logger.error(
            "Missing investigation results in state | incident_id=%s | missing_key=%s",
            state["incident"]["incident_id"],
            e.args[0]
        )
        raise
    for domain, result in results.items():

        logger.info("Processing %s investigation results | incident_id=%s", domain, state["incident"]["incident_id"])
        print(f"Domain: {domain.upper()}")

        print("Agent:", result["agent_name"])

        print("Root cause:", result["probable_root_cause"])

        print("Confidence:", result["confidence"])

        print("Evidence count:", result["unique_evidence_count"])

        print("----------------------------------------")

    return {
        "investigation_results": results
    }


# ------------------------------------------------
# 8. Build parallel LangGraph workflow
# ------------------------------------------------

def build_parallel_workflow():

    graph = StateGraph(IncidentInvestigationState)

    graph.add_node("supervisor", supervisor_node)

    graph.add_node("database", database_node)

    graph.add_node("application", application_node)

    graph.add_node("infrastructure", infrastructure_node)

    graph.add_node("collect_results", collect_results_node)

    # Start workflow
    graph.add_edge(START, "supervisor")

    # FAN-OUT: Three specialist agents execute in parallel
    graph.add_edge("supervisor", "database")

    graph.add_edge("supervisor", "application")

    graph.add_edge("supervisor", "infrastructure")

    # FAN-IN: Wait for all three agents before collection
    graph.add_edge(
        [
            "database",
            "application",
            "infrastructure"
        ],
        "collect_results"
    )

    graph.add_edge("collect_results", END)

    return graph.compile()


# ------------------------------------------------
# 9. Execute workflow
# ------------------------------------------------

if __name__ == "__main__":

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

    app = build_parallel_workflow()

    initial_state = {
        "incident": incident
    }

    print("\n========== PARALLEL INCIDENT WORKFLOW ==========\n")

    workflow_start = perf_counter()

    result = app.invoke(initial_state)

    total_time = perf_counter() - workflow_start

    print("\n========== WORKFLOW EXECUTION SUMMARY ==========\n")

    print("Incident ID:", incident["incident_id"])

    print("Database Agent:", result["database_result"]["confidence"])

    print("Application Agent:", result["application_result"]["confidence"])

    print("Infrastructure Agent:", result["infrastructure_result"]["confidence"])

    print(f"Total workflow execution time: {total_time:.2f} seconds")

    print("\nAll three specialist investigations completed.")
