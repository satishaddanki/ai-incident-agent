# tests/test_mock_enterprise_api.py
import pytest

from app.tools.mock_enterprise_api import (
    ApprovalRequiredError,
    AuthorizationError,
    InvalidActionError,
    MockAPITimeoutError,
    MockEnterpriseAPI,
)


@pytest.fixture
def api():
    return MockEnterpriseAPI()


@pytest.fixture
def payments_engineer():
    return {
        "user_id": "engineer-001",
        "departments": ["payments"],
        "roles": ["incident_investigator"],
    }


@pytest.fixture
def approved_reviewer():
    return {
        "approved": True,
        "reviewer": "reviewer-001",
        "reviewer_roles": ["incident_approver"],
    }


def test_get_incident_authorized_department(
    api,
    payments_engineer,
):
    incident = api.get_incident(
        "INC-1042",
        payments_engineer,
    )

    assert incident["incident_id"] == "INC-1042"
    assert incident["department"] == "payments"


def test_reject_unauthorized_department(
    api,
):
    engineering_user = {
        "user_id": "engineer-002",
        "departments": ["engineering"],
        "roles": ["incident_investigator"],
    }

    with pytest.raises(AuthorizationError):
        api.get_incident(
            "INC-1042",
            engineering_user,
        )


def test_create_recommendation(
    api,
    payments_engineer,
):
    result = api.create_recommendation(
        incident_id="INC-1042",
        recommendation={
            "summary": "Review database connection pool settings",
            "evidence": ["HIST-001"],
        },
        requester=payments_engineer,
    )

    assert result["incident_id"] == "INC-1042"
    assert result["status"] == "PENDING_APPROVAL"


def test_reject_action_without_approval(
    api,
):
    with pytest.raises(ApprovalRequiredError):
        api.execute_corrective_action(
            incident_id="INC-1042",
            action={
                "action_type": "increase_db_connection_pool",
                "parameters": {"pool_size": 30},
            },
            approval={
                "approved": False,
                "reviewer": "reviewer-001",
                "reviewer_roles": ["incident_approver"],
            },
            idempotency_key="test-no-approval",
        )


def test_reject_unauthorized_reviewer(
    api,
):
    with pytest.raises(ApprovalRequiredError):
        api.execute_corrective_action(
            incident_id="INC-1042",
            action={
                "action_type": "increase_db_connection_pool",
                "parameters": {"pool_size": 30},
            },
            approval={
                "approved": True,
                "reviewer": "engineer-001",
                "reviewer_roles": ["incident_investigator"],
            },
            idempotency_key="test-invalid-reviewer",
        )


def test_reject_action_not_in_allowlist(
    api,
    approved_reviewer,
):
    with pytest.raises(InvalidActionError):
        api.execute_corrective_action(
            incident_id="INC-1042",
            action={
                "action_type": "execute_arbitrary_command",
                "parameters": {},
            },
            approval=approved_reviewer,
            idempotency_key="test-invalid-action",
        )


def test_execute_approved_action(
    api,
    approved_reviewer,
):
    result = api.execute_corrective_action(
        incident_id="INC-1042",
        action={
            "action_type": "increase_db_connection_pool",
            "parameters": {"pool_size": 30},
        },
        approval=approved_reviewer,
        idempotency_key="test-action-001",
    )

    assert result["status"] == "SUCCEEDED"
    assert result["approved_by"] == "reviewer-001"


def test_timeout_after_success_does_not_duplicate_action(
    api,
    approved_reviewer,
):
    action = {
        "action_type": "increase_db_connection_pool",
        "parameters": {"pool_size": 30},
    }

    idempotency_key = "test-timeout-001"

    # First call: the mock action succeeds but the response times out.
    with pytest.raises(MockAPITimeoutError):
        api.execute_corrective_action(
            incident_id="INC-1042",
            action=action,
            approval=approved_reviewer,
            idempotency_key=idempotency_key,
            simulate_timeout_after_success=True,
        )

    # Recover by checking the action status.
    status = api.get_action_status(idempotency_key)

    assert status["status"] == "SUCCEEDED"

    # A retry with the same key returns the existing result.
    retry_result = api.execute_corrective_action(
        incident_id="INC-1042",
        action=action,
        approval=approved_reviewer,
        idempotency_key=idempotency_key,
    )

    assert retry_result["action_id"] == status["action_id"]

    # Only one corrective-action event should exist.
    action_events = [
        event
        for event in api.get_audit_events("INC-1042")
        if event["event_type"] == "CORRECTIVE_ACTION_EXECUTED"
    ]

    assert len(action_events) == 1


def test_audit_trail_records_operations(
    api,
    payments_engineer,
):
    api.get_incident("INC-1042", payments_engineer)

    events = api.get_audit_events("INC-1042")

    assert len(events) == 1
    assert events[0]["event_type"] == "INCIDENT_READ"
    assert events[0]["actor"] == "engineer-001"

def test_record_approved_recommendation(
    api,
    payments_engineer,
    approved_reviewer,
):
    recommendation = api.create_recommendation(
        incident_id="INC-1042",
        recommendation={
            "summary": "Increase database connection pool"
        },
        requester=payments_engineer,
    )

    result = api.record_recommendation_decision(
        incident_id="INC-1042",
        recommendation_id=recommendation["recommendation_id"],
        approval=approved_reviewer,
    )

    assert result["status"] == "APPROVED"
    assert result["reviewed_by"] == "reviewer-001"

    events = api.get_audit_events("INC-1042")

    assert any(
        event["event_type"] == "RECOMMENDATION_APPROVED"
        for event in events
    )


def test_record_rejected_recommendation(
    api,
    payments_engineer,
):
    recommendation = api.create_recommendation(
        incident_id="INC-1042",
        recommendation={"summary": "Test recommendation"},
        requester=payments_engineer,
    )

    result = api.record_recommendation_decision(
        incident_id="INC-1042",
        recommendation_id=recommendation["recommendation_id"],
        approval={
            "approved": False,
            "reviewer": "reviewer-001",
            "reviewer_roles": ["incident_approver"],
        },
    )

    assert result["status"] == "REJECTED"


def test_reject_recommendation_for_wrong_incident(
    api,
    payments_engineer,
    approved_reviewer,
):
    recommendation = api.create_recommendation(
        incident_id="INC-1042",
        recommendation={"summary": "Test recommendation"},
        requester=payments_engineer,
    )

    with pytest.raises(AuthorizationError):
        api.record_recommendation_decision(
            incident_id="NEW-INC-2001",
            recommendation_id=recommendation["recommendation_id"],
            approval=approved_reviewer,
        )
