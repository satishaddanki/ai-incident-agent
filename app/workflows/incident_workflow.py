# app/workflows/incident_workflow.py
import json
from typing import TypedDict, Any
from time import perf_counter
from langgraph.graph import StateGraph, START, END  # Correct LangGraph import

from app.rag.resolved_ingestion import ResolvedIncidentIngestor

from app.core.exceptions import (
    ApprovalRequiredError,
    MockAPITimeoutError,
)

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from app.core.logging_config import get_logger

from app.tools.mock_enterprise_api import MockEnterpriseAPI

from app.agents.specialist_agents import (
    DatabaseInvestigationAgent,
    ApplicationInvestigationAgent,
    InfrastructureInvestigationAgent,
)
from app.agents.conflict_resolver import ConflictResolver
from app.agents.remediation_agent import RemediationAgent

logger = get_logger(__name__)
# One shared in-memory API instance for this application process.
enterprise_api = MockEnterpriseAPI()

# ---------------------------------------------------------
# 1. Shared LangGraph state
# ---------------------------------------------------------

class IncidentState(TypedDict, total=False):
    incident: dict
    requester: dict
    service_health: dict

    # Specialist agent results - this is resolved into a consolidated RCA.
    resolved_ingestion_result: dict

    incident_retrieval_status: str
    service_health_status: str

    database_result: dict
    application_result: dict
    infrastructure_result: dict

    investigation_results: dict
    conflict_result: dict
    rca_report: dict
    remediation_plan: dict

    # Enterprise recommendation registration
    recommendation_record: dict
    recommendation_status: str

    approval: dict
    execution_status: str

    # Future enterprise execution fields
    action_result: dict
    action_verification: dict
    audit_events: list

    total_execution_time: float

# ---------------------------------------------------------
# 2. Initialize agents
# ---------------------------------------------------------

database_agent = DatabaseInvestigationAgent()
application_agent = ApplicationInvestigationAgent()
infrastructure_agent = InfrastructureInvestigationAgent()

conflict_resolver = ConflictResolver()
remediation_agent = RemediationAgent()

# ---------------------------------------------------------
# 3.1 Application-controlled remediation action mapping
# ---------------------------------------------------------

def map_remediation_to_action(
    incident: dict,
    rca_report: dict,
    remediation_plan: dict,
) -> dict:

    searchable_context = " ".join([
        str(incident.get("description", "")),
        str(incident.get("logs", "")),
        str(rca_report.get("probable_root_cause", "")),
        str(remediation_plan.get("remediation_summary", "")),
        json.dumps(
            remediation_plan.get("immediate_mitigation", [])
        ),
    ]).lower()

    # Mock environment configuration.
    # This is NOT a production database setting.

    if (
        "connection pool" in searchable_context
        or "pool exhausted" in searchable_context
    ):
        action = {
            "action_type": "increase_db_connection_pool",
            "parameters": {
                "pool_size": 30,
            },
        }

    elif (
        "rollback" in searchable_context
        and "deployment" in searchable_context
    ):
        action = {
            "action_type": "rollback_deployment",
            "parameters": {},
        }

    elif (
        "restart" in searchable_context
        and "application" in searchable_context
    ):
        action = {
            "action_type": "restart_application_instance",
            "parameters": {},
        }

    elif (
        "read only" in searchable_context
        or "read-only" in searchable_context
    ):
        action = {
            "action_type": "enable_read_only_mode",
            "parameters": {},
        }

    else:
        raise ValueError(
            "No sufficiently supported allowlisted remediation "
            "action could be mapped. Manual investigation is required."
        )

    if action["action_type"] not in MockEnterpriseAPI.ALLOWED_ACTIONS:
        raise ValueError("Remediation action is not allowlisted.")

    return action

# ---------------------------------------------------------
# 3. Supervisor
# ---------------------------------------------------------

def supervisor_node(state: IncidentState):
    incident = state["incident"]

    health = state.get("service_health", {})

    logger.info(
        "Supervisor received incident and health information | incident_id=%s",
        incident["incident_id"],
    )

    print("[Supervisor] Incident:", incident["incident_id"])
    print("[Supervisor] Severity:", incident.get("severity"))
    print("[Supervisor] Service:", incident.get("service"))
    print("[Supervisor] Service health:", health.get("status"))
    print("[Supervisor] Error rate:", health.get("error_rate_percent"))
    print("[Supervisor] Dispatching three specialist agents.")

    return {}


# ---------------------------------------------------------
# 3.1 Enterprise API: Incident retrieval
# ---------------------------------------------------------

def incident_retrieval_node(state: IncidentState):

    incident_context = state["incident"]
    requester = state["requester"]

    incident_id = incident_context["incident_id"]

    logger.info(
        "Incident retrieval started | incident_id=%s",
        incident_id,
    )

    try:

        retrieved_incident = enterprise_api.get_incident(
            incident_id=incident_id,
            requester=requester,
        )

        # Preserve useful investigation context, such as logs,
        # while taking incident identity and status from the API.
        incident = {
            **incident_context,
            **retrieved_incident,
        }

        # Normalize API application name to the existing
        # specialist-agent service field.
        incident["service"] = (
            retrieved_incident.get("application")
            or incident_context.get("service")
        )

        logger.info(
            "Incident retrieved successfully | incident_id=%s",
            incident_id,
        )

        return {
            "incident": incident,
            "incident_retrieval_status": "SUCCESS",
        }

    except Exception:

        logger.exception(
            "Incident retrieval failed | incident_id=%s",
            incident_id,
        )

        raise


# ---------------------------------------------------------
# 4. Enterprise API: Service health check
# ---------------------------------------------------------

def service_health_node(state: IncidentState):

    incident = state["incident"]

    incident_id = incident["incident_id"]
    service_name = incident["service"]

    logger.info(
        "Service health check started | incident_id=%s | service=%s",
        incident_id,
        service_name,
    )

    try:

        health = enterprise_api.check_service_health(
            service_name=service_name,
            incident_id=incident_id,
            actor=state["requester"]["user_id"],
        )

        logger.info(
            "Service health retrieved | incident_id=%s | status=%s",
            incident_id,
            health["status"],
        )

        incident_with_health = {**incident, "service_health": health,}

        return {
            "incident": incident_with_health,
            "service_health": health,
            "service_health_status": "SUCCESS",
        }

    except Exception:

        logger.exception(
            "Service health check failed | incident_id=%s",
            incident_id,
        )

        raise

# ---------------------------------------------------------
# 4. Parallel specialist nodes
# ---------------------------------------------------------

def database_node(state: IncidentState):
    start = perf_counter()

    print("\n[Supervisor] Dispatching Database Agent...")
    try:
        result = database_agent.investigate(state["incident"])
    except Exception:
        logger.exception(
            "Database investigation failed | incident_id=%s",
            state["incident"]["incident_id"],
        )
        raise

    if result.get("agent_name") != "Database Investigation Agent":
        raise ValueError("Database agent identity validation failed.")

    result["execution_time_seconds"] = round(
        perf_counter() - start, 2
    )

    return {"database_result": result}


def application_node(state: IncidentState):
    start = perf_counter()

    print("\n[Supervisor] Dispatching Application Agent...")
    try:
        result = application_agent.investigate(state["incident"])
    except Exception:
        logger.exception(
            "Application investigation failed | incident_id=%s",
            state["incident"]["incident_id"],
        )
        raise

    if result.get("agent_name") != "Application Investigation Agent":
        raise ValueError("Application agent identity validation failed.")

    result["execution_time_seconds"] = round(
        perf_counter() - start, 2
    )

    return {"application_result": result}


def infrastructure_node(state: IncidentState):
    start = perf_counter()

    print("\n[Supervisor] Dispatching Infrastructure Agent...")
    try:
        result = infrastructure_agent.investigate(state["incident"])
    except Exception:
        logger.exception(
            "Infrastructure investigation failed | incident_id=%s",
            state["incident"]["incident_id"],
        )
        raise

    if result.get("agent_name") != "Infrastructure Investigation Agent":
        raise ValueError("Infrastructure agent identity validation failed.")

    result["execution_time_seconds"] = round(
        perf_counter() - start, 2
    )

    return {"infrastructure_result": result}


# ---------------------------------------------------------
# 5. Fan-in: collect specialist reports
# ---------------------------------------------------------

def collect_results_node(state: IncidentState):
    print("\n========== FAN-IN: COLLECTING RESULTS ==========")
    logger.info("Collecting investigation results | incident_id=%s", state["incident"]["incident_id"])  
    results = {
        "database": state["database_result"],
        "application": state["application_result"],
        "infrastructure": state["infrastructure_result"],
    }

    for domain, result in results.items():
        logger.info("Processing %s investigation results | incident_id=%s", domain, state["incident"]["incident_id"])
        print(f"\nDomain: {domain.upper()}")
        print("Agent:", result.get("agent_name"))
        print("Root cause:", result.get("probable_root_cause"))
        print("Confidence:", result.get("confidence"))
        print("Evidence count:", result.get("unique_evidence_count", 0))

    return {"investigation_results": results}


# ---------------------------------------------------------
# 6. Conflict resolution and consolidated RCA
# ---------------------------------------------------------

def conflict_resolution_node(state: IncidentState):
    print("\n========== CONFLICT RESOLUTION ==========")

    incident = state["incident"]
    investigation_results = state["investigation_results"]
    logger.info("Resolving conflicts in investigation results | incident_id=%s", incident["incident_id"])
    
    consolidated = conflict_resolver.resolve(
        incident,
        investigation_results,
    )

    # Adapt the consolidated result to the RCA contract
    # expected by the existing RemediationAgent.
    rca_report = {
        "incident_id": incident["incident_id"],
        "incident_summary": (
            f"Incident {incident['incident_id']} affecting "
            f"{incident.get('service', 'unknown service')}: "
            f"{incident.get('description', '')}"
        ),
        "probable_root_cause": consolidated.get(
            "consolidated_root_cause",
            "Unable to determine root cause.",
        ),
        "supporting_evidence": consolidated.get(
            "supporting_evidence", []
        ),
        "confidence": consolidated.get("confidence", "Low"),
        "reasoning": consolidated.get("resolution_summary", ""),
        "recommended_actions": consolidated.get(
            "additional_investigation_required", []
        ),
        "missing_information": [
            "Current system verification is required."
        ] if not consolidated.get("current_root_cause_verified") else [],
        "requires_human_investigation": consolidated.get(
            "requires_human_review", True
        ),
        "conflict_detected": consolidated.get(
            "conflict_detected", False
        ),
        "current_root_cause_verified": consolidated.get(
            "current_root_cause_verified", False
        ),
        "root_cause_status": consolidated.get(
            "root_cause_status",
            "UNVERIFIED_HYPOTHESIS"
        ),
    }

    print("\n[Workflow] Consolidated RCA prepared.")
    print("[Workflow] Root cause status:", rca_report["root_cause_status"])
    print("[Workflow] Conflict detected:", rca_report["conflict_detected"])
    print("[Workflow] Confidence:", rca_report["confidence"])

    return {
        "conflict_result": consolidated,
        "rca_report": rca_report,
    }


# ---------------------------------------------------------
# 7. Remediation planning
# ---------------------------------------------------------

def remediation_node(state: IncidentState):
    print("\n========== REMEDIATION PLANNING ==========")

    rca_report = state["rca_report"]

    plan = remediation_agent.generate_plan(rca_report)

    # Application-controlled fields; do not trust LLM values.
    plan["incident_id"] = state["incident"]["incident_id"]
    plan["requires_human_approval"] = True
    plan["execution_status"] = "NOT_EXECUTED"

    print("[Remediation] Plan generated.")
    print("[Remediation] Human approval is mandatory.")
    print("[Remediation] No production action has been executed.")

    return {"remediation_plan": plan}


# ---------------------------------------------------------
# 7.1 Enterprise API: Recommendation registration
# ---------------------------------------------------------

def recommendation_registration_node(state: IncidentState):

    incident = state["incident"]
    plan = state["remediation_plan"]
    requester = state["requester"]

    incident_id = incident["incident_id"]

    print("\n========== ENTERPRISE RECOMMENDATION REGISTRATION ==========")

    logger.info(
        "Registering remediation recommendation | incident_id=%s",
        incident_id,
    )

    try:

        recommendation_record = enterprise_api.create_recommendation(
            incident_id=incident_id,
            recommendation=plan,
            requester=requester,
        )

        logger.info(
            "Recommendation registered successfully | incident_id=%s | recommendation_id=%s",
            incident_id,
            recommendation_record["recommendation_id"],
        )

        print(
            "[Enterprise API] Recommendation registered:",
            recommendation_record["recommendation_id"],
        )

        print(
            "[Enterprise API] Recommendation status:",
            recommendation_record["status"],
        )

        return {
            "recommendation_record": recommendation_record,
            "recommendation_status": "SUCCESS",
        }

    except Exception:

        logger.exception(
            "Recommendation registration failed | incident_id=%s",
            incident_id,
        )

        raise


# ---------------------------------------------------------
# 8. Human approval interrupt
# ---------------------------------------------------------

def approval_node(state: IncidentState):

    incident = state["incident"]
    plan = state["remediation_plan"]
    recommendation = state["recommendation_record"]

    approval_request = {
        "message": "Human approval is required before remediation.",
        "incident_id": incident["incident_id"],
        "recommendation_id": recommendation["recommendation_id"],
        "recommendation_status": recommendation["status"],
        "severity": incident.get("severity"),
        "remediation_summary": plan.get("remediation_summary"),
        "requires_human_approval": True,
        "execution_status": "NOT_EXECUTED",
    }

    print("\n========== HUMAN APPROVAL REQUIRED ==========")
    print(json.dumps(approval_request, indent=2))

    decision = interrupt(approval_request)

    if not isinstance(decision, dict):
        decision = {"approved": False}

    decision = {
        **decision,
        "approved": decision.get("approved") is True,
    }

    # Bind approval to the recommendation stored by the enterprise API.
    if (
        decision.get("recommendation_id")
        != recommendation["recommendation_id"]
    ):
        raise ApprovalRequiredError(
            "Approval recommendation ID does not match."
        )

    approved_record = enterprise_api.record_recommendation_decision(
        incident_id=incident["incident_id"],
        recommendation_id=recommendation["recommendation_id"],
        approval=decision,
    )

    decision["recommendation_id"] = (
        approved_record["recommendation_id"]
    )

    print(
        "[Enterprise API] Human decision recorded:",
        approved_record["status"],
    )

    return {
        "approval": decision,
        "recommendation_record": approved_record,
    }
# ---------------------------------------------------------
# 9. Approved corrective-action execution
# ---------------------------------------------------------

def approved_node(state: IncidentState):

    incident = state["incident"]
    approval = state["approval"]
    recommendation = state["recommendation_record"]

    incident_id = incident["incident_id"]
    recommendation_id = recommendation["recommendation_id"]

    print("\n========== CORRECTIVE ACTION EXECUTION ==========")

    # Validate approval.
    if approval.get("approved") is not True:
        raise ApprovalRequiredError(
            "Corrective action requires explicit human approval."
        )

    if approval.get("recommendation_id") != recommendation_id:
        raise ApprovalRequiredError(
            "Approval does not match the registered recommendation."
        )

    if recommendation.get("status") != "APPROVED":
        raise ApprovalRequiredError(
            "Enterprise recommendation is not approved."
        )

    # Convert descriptive remediation into a controlled API action.
    action = map_remediation_to_action(
        incident=incident,
        rca_report=state["rca_report"],
        remediation_plan=state["remediation_plan"],
    )

    print("[Action Mapper] Selected action:", action["action_type"])

    # Deterministic key prevents duplicate execution on retries.
    idempotency_key = (
        f"{incident_id}:{recommendation_id}"
    )

    try:

        result = enterprise_api.execute_corrective_action(
            incident_id=incident_id,
            action=action,
            approval=approval,
            idempotency_key=idempotency_key,
        )

    except MockAPITimeoutError:

        logger.warning(
            "Corrective action response timed out. "
            "Checking existing action status before retrying."
        )

        result = enterprise_api.get_action_status(
            idempotency_key
        )

        if result.get("status") != "SUCCEEDED":
            raise

        print(
            "[Recovery] Existing successful action recovered."
        )

    logger.info(
        "Corrective action execution completed | incident_id=%s | action_id=%s",
        incident_id,
        result["action_id"],
    )

    print("[Enterprise API] Action ID:", result["action_id"])
    print("[Enterprise API] Action status:", result["status"])

    return {
        "action_result": result,
        "execution_status": result["status"],
    }

# ---------------------------------------------------------
# 9. Approval routing
# ---------------------------------------------------------

def route_after_approval(state: IncidentState):
    approval = state.get("approval", {})

    if approval.get("approved") is True:
        return "approved"

    return "rejected"


# def approved_node(state: IncidentState):
#     print("\n[Workflow] Remediation plan APPROVED.")
#     print("[Workflow] Status: APPROVED_PENDING_EXECUTION")
#     print("[Workflow] Execution remains disabled in this demo.")

#     return {
#         "execution_status": "APPROVED_PENDING_EXECUTION"
#     }


def rejected_node(state: IncidentState):
    print("\n[Workflow] Remediation plan REJECTED.")
    print("[Workflow] No remediation action was executed.")

    return {"execution_status": "REJECTED"}

# ---------------------------------------------------------
# 10. Action status verification
# ---------------------------------------------------------

def action_verification_node(state: IncidentState):

    action_result = state["action_result"]

    idempotency_key = action_result["idempotency_key"]

    print("\n========== ACTION STATUS VERIFICATION ==========")

    verification = enterprise_api.get_action_status(
        idempotency_key
    )

    print(
        "[Enterprise API] Verified action status:",
        verification["status"],
    )

    if verification.get("status") != "SUCCEEDED":
        logger.error(
            "Corrective action verification failed | incident_id=%s",
            state["incident"]["incident_id"],
        )

        return {
            "action_verification": verification,
            "execution_status": "VERIFICATION_FAILED",
        }

    return {
        "action_verification": verification,
        "execution_status": "VERIFIED_SUCCESS",
    }

# ---------------------------------------------------------
# 11. Enterprise audit trail
# ---------------------------------------------------------

def audit_trail_node(state: IncidentState):

    incident_id = state["incident"]["incident_id"]

    print("\n========== ENTERPRISE AUDIT TRAIL ==========")

    events = enterprise_api.get_audit_events(
        incident_id=incident_id
    )

    for event in events:

        print(
            event["event_type"],
            "|",
            event["actor"],
            "|",
            event["timestamp"],
        )

    logger.info(
        "Audit trail retrieved | incident_id=%s | event_count=%s",
        incident_id,
        len(events),
    )

    return {
        "audit_events": events,
    }


# ---------------------------------------------------------
# 11.1.0 Verified resolved incident ingestion
# ---------------------------------------------------------

def resolved_incident_ingestion_node(state: IncidentState):

    incident_id = state["incident"]["incident_id"]

    print("\n========== RESOLVED INCIDENT INGESTION ==========")

    recommendation = dict(
        state.get("recommendation_record") or {}
    )

    # Support the workflow's top-level recommendation status.
    if not recommendation.get("status"):
        recommendation["status"] = state.get(
            "recommendation_status"
        )

    record = {
        "incident": state.get("incident", {}),
        "rca_report": state.get("rca_report", {}),
        "remediation_plan": state.get(
            "remediation_plan", {}
        ),
        "recommendation_record": recommendation,
        "execution_status": state.get(
            "execution_status"
        ),
        "action_result": state.get(
            "action_result", {}
        ),
        "action_verification": state.get(
            "action_verification", {}
        ),
    }

    try:

        ingestor = ResolvedIncidentIngestor()

        result = ingestor.ingest(record)

        print(
            "[RAG Ingestion] Incident successfully indexed:",
            incident_id,
        )

        print(
            "[RAG Ingestion] Vectors submitted:",
            result["vectors_submitted"],
        )

        return {
            "resolved_ingestion_result": result
        }

    except ValueError as exc:

        print(
            "[RAG Ingestion] Incident not eligible:",
            str(exc),
        )

        return {
            "resolved_ingestion_result": {
                "incident_id": incident_id,
                "status": "SKIPPED",
                "reason": str(exc),
            }
        }

    except Exception as exc:

        logger.exception(
            "Resolved incident ingestion failed | incident_id=%s",
            incident_id,
        )

        # Do not undo an already completed remediation
        # because the knowledge indexing operation failed.
        return {
            "resolved_ingestion_result": {
                "incident_id": incident_id,
                "status": "FAILED",
                "reason": str(exc),
            }
        }


# ---------------------------------------------------------
# 12. Build unified LangGraph
# ---------------------------------------------------------

def build_incident_workflow():
    graph = StateGraph(IncidentState)
    graph.add_node("incident_retrieval", incident_retrieval_node,)

    graph.add_node("service_health", service_health_node,)
    graph.add_node("supervisor", supervisor_node)

    graph.add_node("database", database_node)
    graph.add_node("application", application_node)
    graph.add_node("infrastructure", infrastructure_node)

    graph.add_node("collect_results", collect_results_node)
    graph.add_node("conflict_resolution", conflict_resolution_node,)
    graph.add_node("remediation", remediation_node,)
    graph.add_node("recommendation_registration", recommendation_registration_node,)
    graph.add_node("approval", approval_node,)

    graph.add_node("approved", approved_node,)

    graph.add_node("action_verification", action_verification_node,)

    graph.add_node("audit_trail", audit_trail_node)

    graph.add_node("resolved_ingestion", resolved_incident_ingestion_node,)

    graph.add_node("rejected", rejected_node)

    # Enterprise API integration
    graph.add_edge(START, "incident_retrieval")
    graph.add_edge("incident_retrieval", "service_health",)
    graph.add_edge("service_health", "supervisor", )

    # Fan-out
    graph.add_edge("supervisor", "database")
    graph.add_edge("supervisor", "application")
    graph.add_edge("supervisor", "infrastructure")

    # Fan-in: wait for all three specialists
    graph.add_edge(
        ["database", "application", "infrastructure"],
        "collect_results",
    )

    graph.add_edge("collect_results", "conflict_resolution")
    graph.add_edge("conflict_resolution", "remediation")
    graph.add_edge("remediation", "recommendation_registration")
    graph.add_edge("recommendation_registration", "approval",)

    # Conditional routing based on human approval
    graph.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "approved": "approved",
            "rejected": "rejected",
        },
    )

    # Approved execution path
    graph.add_edge("approved", "action_verification",)

    graph.add_edge("action_verification", "audit_trail", )

    # Rejected path also produces an audit trail.
    graph.add_edge("rejected", "audit_trail",)

    graph.add_edge("audit_trail", "resolved_ingestion",)

    graph.add_edge("resolved_ingestion", END,)

    checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)

# ---------------------------------------------------------
# 11. Local end-to-end execution
# ---------------------------------------------------------

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
        ),
    }

    requester = {
        "user_id": "engineer-001",
        "departments": ["payments"],
        "roles": ["incident_investigator"],
    }
    workflow = build_incident_workflow()

    config = {
        "configurable": {
            "thread_id": incident["incident_id"]
        }
    }

    initial_state = {"incident": incident, "requester": requester,}

    print("\n========== ENTERPRISE INCIDENT WORKFLOW ==========")

    start = perf_counter()

    result = workflow.invoke(initial_state, config=config)

    # A graph interrupt pauses execution and returns control here.
    snapshot = workflow.get_state(config)

    if snapshot.tasks and any(
        task.interrupts for task in snapshot.tasks
    ):
        print("\n========== REVIEW REMEDIATION PLAN ==========")
        print("\n========== HUMAN APPROVAL REQUIRED ==========")

        print(
            json.dumps(
                snapshot.values.get("remediation_plan", {}),
                indent=2,
            )
        )

        answer = input(
            "\nApprove remediation plan? (yes/no): "
        ).strip().lower()

        approved = answer in {"yes", "y"}

    recommendation_id = (
        snapshot.values["recommendation_record"]["recommendation_id"]
    )

    result = workflow.invoke(
        Command(
            resume={
                "approved": approved,
                "reviewer": "local-demo-reviewer",
                "reviewer_roles": ["incident_approver"],
                "recommendation_id": recommendation_id,
            }
        ),
        config=config,
    )

    elapsed = perf_counter() - start

    print("\n========== FINAL WORKFLOW SUMMARY ==========")

    print("Incident:", incident["incident_id"])

    print(
        "Recommendation ID:",
        result.get("recommendation_record", {}).get(
            "recommendation_id"
        ),
    )

    print(
        "Recommendation status:",
        result.get("recommendation_record", {}).get("status"),
    )

    print(
        "Execution status:",
        result.get("execution_status"),
    )

    print(
        "Action ID:",
        result.get("action_result", {}).get("action_id", "N/A"),
    )

    print(
        "Verified status:",
        result.get("action_verification", {}).get("status", "N/A"),
    )

    print(
        "Audit event count:",
        len(result.get("audit_events", [])),
    )

    print(
        "Total elapsed time:",
        round(elapsed, 2),
        "seconds",
    )

    print("\n========== ENTERPRISE AUDIT EVENTS ==========")

    audit_events = enterprise_api.get_audit_events(
        incident_id=incident["incident_id"]
    )

    for event in audit_events:
        print(
            event["event_type"],
            "|",
            event["actor"],
            "|",
            event["timestamp"],
        )
