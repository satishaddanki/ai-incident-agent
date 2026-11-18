# app/tools/mock_enterprise_api.py
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

from app.core.exceptions import (
    EnterpriseAPIError,
    AuthorizationError,
    ApprovalRequiredError,
    InvalidActionError,
    MockAPITimeoutError,
)

class MockEnterpriseAPI:
    """
    Simulates enterprise incident-management APIs.

    All data is stored in memory. No real infrastructure changes are made.
    """

    ALLOWED_ACTIONS = {
        "increase_db_connection_pool",
        "restart_application_instance",
        "rollback_deployment",
        "enable_read_only_mode",
    }

    def __init__(self) -> None:
        self._lock = Lock()

        # Mock incident-management system.
        self._incidents: dict[str, dict[str, Any]] = {
            "INC-1042": {
                "incident_id": "INC-1042",
                "application": "Payment Processing Service",
                "severity": "P1",
                "department": "payments",
                "status": "OPEN",
                "description": (
                    "Payment transactions are failing intermittently. "
                    "Error rates increased to 35% after a recent deployment."
                ),
            },
            "NEW-INC-2001": {
                "incident_id": "NEW-INC-2001",
                "application": "PaymentService",
                "severity": "P1",
                "department": "payments",
                "status": "OPEN",
                "description": (
                    "Database connection timeouts are affecting "
                    "the payment application."
                ),
            },
        }

        # Mock service-health information.
        self._service_health: dict[str, dict[str, Any]] = {
            "Payment Processing Service": {
                "service_name": "Payment Processing Service",
                "status": "DEGRADED",
                "error_rate_percent": 35,
                "database_connectivity": "INTERMITTENT",
            },
            "PaymentService": {
                "service_name": "PaymentService",
                "status": "DEGRADED",
                "error_rate_percent": 28,
                "database_connectivity": "INTERMITTENT",
            },
        }

        self._recommendations: dict[str, dict[str, Any]] = {}

        # Idempotency key -> completed action result.
        self._actions: dict[str, dict[str, Any]] = {}

        # In-memory audit events.
        self._audit_events: list[dict[str, Any]] = []

    def register_incident(
        self,
        incident: dict[str, Any],
        requester: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Register an incident submitted through the demo API.

        Existing seeded incidents are preserved and never overwritten.
        New services receive UNKNOWN health until actual health data
        is supplied.
        """

        incident_id = incident.get("incident_id")
        service_name = incident.get("service")
        department = (
            incident.get("department")
            or next(iter(requester.get("departments", [])), None)
        )

        if not incident_id:
            raise EnterpriseAPIError("Incident ID is required.")

        if not service_name:
            raise EnterpriseAPIError("Service name is required.")

        if not department:
            raise EnterpriseAPIError(
                "Incident department is required."
            )

        with self._lock:

            # Preserve existing seeded incident records.
            existing = self._incidents.get(incident_id)

            if existing is not None:
                self._check_incident_access(existing, requester)
                return deepcopy(existing)

            incident_record = {
                "incident_id": incident_id,
                "application": service_name,
                "service": service_name,
                "severity": incident.get("severity", "P1"),
                "department": department,
                "status": "OPEN",
                "description": incident.get("description", ""),
                "logs": incident.get("logs", ""),
            }

            self._check_incident_access(
                incident_record,
                requester,
            )

            self._incidents[incident_id] = incident_record

            # Do not invent service-health measurements.
            # Mark health as UNKNOWN until actual data is available.
            if service_name not in self._service_health:
                self._service_health[service_name] = {
                    "service_name": service_name,
                    "status": "UNKNOWN",
                    "error_rate_percent": None,
                    "database_connectivity": "UNKNOWN",
                }

            self._record_audit(
                event_type="INCIDENT_REGISTERED",
                incident_id=incident_id,
                actor=requester["user_id"],
                details={
                    "service_name": service_name,
                    "department": department,
                    "status": "OPEN",
                },
            )

            return deepcopy(incident_record)

    def _record_audit(
        self,
        event_type: str,
        incident_id: str,
        actor: str,
        details: dict[str, Any],
    ) -> None:
        """Record an auditable event."""

        event = {
            "event_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "incident_id": incident_id,
            "actor": actor,
            "details": deepcopy(details),
        }

        self._audit_events.append(event)

    @staticmethod
    def _check_incident_access(
        incident: dict[str, Any],
        requester: dict[str, Any],
    ) -> None:
        """Enforce department-level access to incident information."""

        requester_id = requester.get("user_id")
        requester_roles = requester.get("roles", [])
        requester_departments = requester.get("departments", [])

        if not requester_id:
            raise AuthorizationError("Requester identity is required.")

        if "incident_admin" in requester_roles:
            return

        incident_department = incident["department"]

        if incident_department not in requester_departments:
            raise AuthorizationError(
                "Access denied: requester is not authorized "
                f"for department '{incident_department}'."
            )

    def get_incident(
        self,
        incident_id: str,
        requester: dict[str, Any],
    ) -> dict[str, Any]:
        """Retrieve an incident after checking department authorization."""

        with self._lock:
            incident = self._incidents.get(incident_id)

            if incident is None:
                raise EnterpriseAPIError(
                    f"Incident '{incident_id}' was not found."
                )

            self._check_incident_access(incident, requester)

            self._record_audit(
                event_type="INCIDENT_READ",
                incident_id=incident_id,
                actor=requester["user_id"],
                details={"department": incident["department"]},
            )

            return deepcopy(incident)

   
    def check_service_health(
        self,
        service_name: str,
        incident_id: str = "N/A",
        actor: str = "mock-enterprise-api",
    ) -> dict[str, Any]:
        """Retrieve mocked service-health information."""

        with self._lock:

            health = self._service_health.get(service_name)

            if health is None:
                raise EnterpriseAPIError(
                    f"Service '{service_name}' was not found."
                )

            self._record_audit(
                event_type="SERVICE_HEALTH_CHECK",
                incident_id=incident_id,
                actor=actor,
                details={
                    "service_name": service_name,
                    "status": health["status"],
                },
            )

            return deepcopy(health)

    def create_recommendation(
        self,
        incident_id: str,
        recommendation: dict[str, Any],
        requester: dict[str, Any],
    ) -> dict[str, Any]:
        """Save a remediation recommendation for an authorized incident."""

        with self._lock:
            incident = self._incidents.get(incident_id)

            if incident is None:
                raise EnterpriseAPIError(
                    f"Incident '{incident_id}' was not found."
                )

            self._check_incident_access(incident, requester)

            recommendation_id = f"REC-{uuid4().hex[:10].upper()}"

            record = {
                "recommendation_id": recommendation_id,
                "incident_id": incident_id,
                "recommendation": deepcopy(recommendation),
                "status": "PENDING_APPROVAL",
                "created_by": requester["user_id"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            self._recommendations[recommendation_id] = record

            self._record_audit(
                event_type="RECOMMENDATION_CREATED",
                incident_id=incident_id,
                actor=requester["user_id"],
                details={
                    "recommendation_id": recommendation_id,
                    "status": record["status"],
                },
            )

            return deepcopy(record)

    def record_recommendation_decision(
        self,
        incident_id: str,
        recommendation_id: str,
        approval: dict[str, Any],
    ) -> dict[str, Any]:
        """Record an authorized human decision against a recommendation."""

        with self._lock:

            recommendation = self._recommendations.get(
                recommendation_id
            )

            if recommendation is None:
                raise EnterpriseAPIError(
                    f"Recommendation '{recommendation_id}' was not found."
                )

            if recommendation["incident_id"] != incident_id:
                raise AuthorizationError(
                    "Recommendation does not belong to this incident."
                )

            if recommendation["status"] != "PENDING_APPROVAL":
                raise EnterpriseAPIError(
                    "Recommendation has already received a decision."
                )

            reviewer = approval.get("reviewer")
            reviewer_roles = approval.get("reviewer_roles", [])

            if not reviewer:
                raise ApprovalRequiredError(
                    "An identified human reviewer is required."
                )

            if not (
                "incident_approver" in reviewer_roles
                or "incident_admin" in reviewer_roles
            ):
                raise ApprovalRequiredError(
                    "Reviewer is not authorized to decide this recommendation."
                )

            decision = approval.get("approved") is True

            recommendation["status"] = (
                "APPROVED" if decision else "REJECTED"
            )

            recommendation["reviewed_by"] = reviewer

            recommendation["reviewed_at"] = (
                datetime.now(timezone.utc).isoformat()
            )

            self._record_audit(
                event_type=(
                    "RECOMMENDATION_APPROVED"
                    if decision
                    else "RECOMMENDATION_REJECTED"
                ),
                incident_id=incident_id,
                actor=reviewer,
                details={
                    "recommendation_id": recommendation_id,
                    "status": recommendation["status"],
                },
            )

            return deepcopy(recommendation)

    def execute_corrective_action(
        self,
        incident_id: str,
        action: dict[str, Any],
        approval: dict[str, Any],
        idempotency_key: str,
        simulate_timeout_after_success: bool = False,
    ) -> dict[str, Any]:
        """
        Simulate an approved corrective action.

        A timeout can be raised after the action is recorded as successful.
        Retrying with the same idempotency key will not execute it twice.
        """

        with self._lock:
            if not idempotency_key:
                raise EnterpriseAPIError(
                    "An idempotency key is required."
                )

            # Return an existing result rather than executing twice.
            existing_result = self._actions.get(idempotency_key)

            if existing_result is not None:
                return deepcopy(existing_result)

            incident = self._incidents.get(incident_id)

            if incident is None:
                raise EnterpriseAPIError(
                    f"Incident '{incident_id}' was not found."
                )

            if approval.get("approved") is not True:
                raise ApprovalRequiredError(
                    "Corrective action cannot execute without approval."
                )

            reviewer = approval.get("reviewer")

            if not reviewer:
                raise ApprovalRequiredError(
                    "An identified human reviewer is required."
                )

            reviewer_roles = approval.get("reviewer_roles", [])

            if not (
                "incident_approver" in reviewer_roles
                or "incident_admin" in reviewer_roles
            ):
                raise ApprovalRequiredError(
                    "Reviewer does not have the incident_approver role."
                )

            action_type = action.get("action_type")

            if action_type not in self.ALLOWED_ACTIONS:
                raise InvalidActionError(
                    f"Action '{action_type}' is not allowlisted."
                )

            action_id = f"ACT-{uuid4().hex[:10].upper()}"

            # This represents a simulated successful enterprise operation.
            result = {
                "action_id": action_id,
                "incident_id": incident_id,
                "action_type": action_type,
                "parameters": deepcopy(action.get("parameters", {})),
                "status": "SUCCEEDED",
                "approved_by": reviewer,
                "idempotency_key": idempotency_key,
                "executed_at": datetime.now(timezone.utc).isoformat(),
            }

            # Persist the result before simulating a response timeout.
            self._actions[idempotency_key] = result

            self._record_audit(
                event_type="CORRECTIVE_ACTION_EXECUTED",
                incident_id=incident_id,
                actor=reviewer,
                details={
                    "action_id": action_id,
                    "action_type": action_type,
                    "status": "SUCCEEDED",
                    "idempotency_key": idempotency_key,
                },
            )

            if simulate_timeout_after_success:
                raise MockAPITimeoutError(
                    "The mock API timed out after the action succeeded. "
                    "Check action status before retrying."
                )

            return deepcopy(result)

    def get_action_status(
        self,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """Retrieve and audit the status of an executed action."""

        with self._lock:

            result = self._actions.get(idempotency_key)

            if result is None:
                return {
                    "idempotency_key": idempotency_key,
                    "status": "NOT_FOUND",
                }

            self._record_audit(
                event_type="ACTION_STATUS_VERIFIED",
                incident_id=result["incident_id"],
                actor="mock-enterprise-api",
                details={
                    "action_id": result["action_id"],
                    "status": result["status"],
                },
            )

            return deepcopy(result)

    def get_audit_events(
        self,
        incident_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve audit events, optionally filtered by incident."""

        with self._lock:
            events = self._audit_events

            if incident_id is not None:
                events = [
                    event
                    for event in events
                    if event["incident_id"] == incident_id
                ]

            return deepcopy(events)


if __name__ == "__main__":
    api = MockEnterpriseAPI()

    payments_engineer = {
        "user_id": "engineer-001",
        "departments": ["payments"],
        "roles": ["incident_investigator"],
    }

    incident = api.get_incident("INC-1042", payments_engineer)
    print("Incident retrieved:", incident["incident_id"])

    health = api.check_service_health(
        "Payment Processing Service"
    )
    print("Service health:", health["status"])
