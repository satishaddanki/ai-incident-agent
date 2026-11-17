# app/main.py
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from langgraph.types import Command

from app.core.exceptions import (
    AuthorizationError,
    ApprovalRequiredError,
    InvalidActionError,
    MockAPITimeoutError,
    WorkflowExecutionError,
)

from app.workflows.incident_workflow import (
    build_incident_workflow,
    enterprise_api,
)


# =========================================================
# 1. FastAPI application
# =========================================================

app = FastAPI(
    title="AI Incident Investigation and Remediation API",
    description=(
        "Enterprise-style multi-agent incident investigation "
        "with human approval, controlled remediation and audit."
    ),
    version="1.0.0",
)


# =========================================================
# 2. Compile the LangGraph workflow ONCE
# =========================================================

# Important:
# Keep this shared instance alive for the entire application
# process. Its MemorySaver stores interrupted workflow state.

workflow = build_incident_workflow()


# =========================================================
# 3. Pydantic request models
# =========================================================

class IncidentDetails(BaseModel):
    incident_id: str = Field(min_length=1)
    severity: str = Field(default="P1")
    service: str = Field(min_length=1)
    description: str = ""
    logs: str = ""


class RequesterDetails(BaseModel):
    user_id: str = Field(min_length=1)
    departments: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)


class InvestigationRequest(BaseModel):
    incident: IncidentDetails
    requester: RequesterDetails


class ApprovalRequest(BaseModel):
    reviewer: str = Field(min_length=1)
    departments: list[str] = Field(default_factory=list)
    reviewer_roles: list[str] = Field(default_factory=list)


# =========================================================
# 4. Common helper functions
# =========================================================

def get_thread_config(thread_id: str) -> dict:
    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def get_workflow_snapshot(thread_id: str):
    config = get_thread_config(thread_id)
    return workflow.get_state(config)


def extract_interrupts(snapshot) -> list:
    interrupts = []

    if snapshot.tasks:
        for task in snapshot.tasks:
            for interrupt_item in task.interrupts:
                interrupts.append(interrupt_item.value)

    return interrupts


def validate_incident_access(
    incident_id: str,
    user_id: str,
    departments: list[str],
    roles: list[str],
):
    requester = {
        "user_id": user_id,
        "departments": departments,
        "roles": roles,
    }

    enterprise_api.get_incident(
        incident_id,
        requester,
    )


def handle_api_exception(exc: Exception):
    if isinstance(exc, AuthorizationError):
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    if isinstance(exc, ApprovalRequiredError):
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    if isinstance(exc, InvalidActionError):
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if isinstance(exc, MockAPITimeoutError):
        raise HTTPException(
            status_code=504,
            detail=str(exc),
        )

    if isinstance(exc, WorkflowExecutionError):
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    raise HTTPException(
        status_code=500,
        detail="Internal incident workflow error.",
    )


# =========================================================
# 5. Health endpoint
# =========================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "application": "AI Incident Agent",
        "workflow": "LangGraph",
    }


# =========================================================
# 6. Start incident investigation
# =========================================================

@app.post("/incidents/investigate")
def investigate_incident(
    request: InvestigationRequest,
):

    incident = request.incident.model_dump()
    requester = request.requester.model_dump()

    incident_id = incident["incident_id"]

    config = get_thread_config(incident_id)

    try:
        # Prevent accidentally starting a second workflow
        # with the same thread ID in this process.

        existing_snapshot = workflow.get_state(config)

        if existing_snapshot.values:
            raise HTTPException(
                status_code=409,
                detail=(
                    "A workflow already exists for this incident ID."
                ),
            )

        initial_state = {
            "incident": incident,
            "requester": requester,
        }

        result = workflow.invoke(
            initial_state,
            config=config,
        )

        snapshot = workflow.get_state(config)

        interrupts = extract_interrupts(snapshot)

        return {
            "message": "Incident investigation completed.",
            "incident_id": incident_id,
            "thread_id": incident_id,
            "status": (
                "WAITING_FOR_HUMAN_APPROVAL"
                if interrupts
                else "COMPLETED"
            ),
            "approval_required": bool(interrupts),
            "approval_request": interrupts,
            "workflow_result": snapshot.values or result,
        }

    except HTTPException:
        raise

    except Exception as exc:
        handle_api_exception(exc)


# =========================================================
# 7. Retrieve workflow status
# =========================================================

@app.get("/incidents/{thread_id}/status")
def get_incident_status(
    thread_id: str,
):

    try:
        snapshot = get_workflow_snapshot(thread_id)

        if not snapshot.values:
            raise HTTPException(
                status_code=404,
                detail="Incident workflow not found.",
            )

        state = snapshot.values

        incident = state.get("incident", {})
        requester = state.get("requester", {})

        # Enforce the original requester's incident access.
        validate_incident_access(
            incident_id=thread_id,
            user_id=requester.get("user_id", ""),
            departments=requester.get("departments", []),
            roles=requester.get("roles", []),
        )

        interrupts = extract_interrupts(snapshot)

        return {
            "thread_id": thread_id,
            "incident_id": incident.get("incident_id"),
            "status": (
                "WAITING_FOR_HUMAN_APPROVAL"
                if interrupts
                else "COMPLETED"
            ),
            "next_nodes": list(snapshot.next),
            "approval_required": bool(interrupts),
            "approval_request": interrupts,
            "workflow_state": state,
        }

    except HTTPException:
        raise

    except Exception as exc:
        handle_api_exception(exc)


# =========================================================
# 8. Common approval / rejection implementation
# =========================================================

def process_human_decision(
    thread_id: str,
    request: ApprovalRequest,
    approved: bool,
):

    config = get_thread_config(thread_id)

    try:
        snapshot = workflow.get_state(config)

        if not snapshot.values:
            raise HTTPException(
                status_code=404,
                detail="Incident workflow not found.",
            )

        interrupts = extract_interrupts(snapshot)

        if not interrupts:
            raise HTTPException(
                status_code=409,
                detail=(
                    "No pending human approval exists "
                    "for this incident."
                ),
            )

        state = snapshot.values

        recommendation = state.get(
            "recommendation_record",
            {},
        )

        recommendation_id = recommendation.get(
            "recommendation_id"
        )

        if not recommendation_id:
            raise HTTPException(
                status_code=409,
                detail="Recommendation ID is missing.",
            )

        # Validate reviewer access to the incident.
        validate_incident_access(
            incident_id=thread_id,
            user_id=request.reviewer,
            departments=request.departments,
            roles=request.reviewer_roles,
        )

        # Resume the existing interrupted workflow.
        result = workflow.invoke(
            Command(
                resume={
                    "approved": approved,
                    "reviewer": request.reviewer,
                    "reviewer_roles": request.reviewer_roles,
                    "recommendation_id": recommendation_id,
                }
            ),
            config=config,
        )

        final_snapshot = workflow.get_state(config)

        final_state = (
            final_snapshot.values or result
        )

        return {
            "message": (
                "Remediation approved."
                if approved
                else "Remediation rejected."
            ),
            "incident_id": thread_id,
            "recommendation_id": recommendation_id,
            "recommendation_status": final_state.get(
                "recommendation_status"
            ),
            "execution_status": final_state.get(
                "execution_status"
            ),
            "action_result": final_state.get(
                "action_result"
            ),
            "action_verification": final_state.get(
                "action_verification"
            ),
            "resolved_ingestion_result": final_state.get(
                "resolved_ingestion_result"
            ),
            "audit_events": final_state.get(
                "audit_events",
                [],
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:
        handle_api_exception(exc)


# =========================================================
# 9. Approve remediation
# =========================================================

@app.post("/incidents/{thread_id}/approve")
def approve_remediation(
    thread_id: str,
    request: ApprovalRequest,
):

    return process_human_decision(
        thread_id=thread_id,
        request=request,
        approved=True,
    )


# =========================================================
# 10. Reject remediation
# =========================================================

@app.post("/incidents/{thread_id}/reject")
def reject_remediation(
    thread_id: str,
    request: ApprovalRequest,
):

    return process_human_decision(
        thread_id=thread_id,
        request=request,
        approved=False,
    )


# =========================================================
# 11. Retrieve incident audit history
# =========================================================

@app.get("/incidents/{incident_id}/audit")
def get_incident_audit(
    incident_id: str,
    user_id: str = Query(min_length=1),
    departments: list[str] = Query(default=[]),
    roles: list[str] = Query(default=[]),
):

    try:
        # Verify access before exposing audit information.
        validate_incident_access(
            incident_id=incident_id,
            user_id=user_id,
            departments=departments,
            roles=roles,
        )

        events = enterprise_api.get_audit_events(
            incident_id=incident_id,
        )

        return {
            "incident_id": incident_id,
            "total_events": len(events),
            "audit_events": events,
        }

    except HTTPException:
        raise

    except Exception as exc:
        handle_api_exception(exc)
