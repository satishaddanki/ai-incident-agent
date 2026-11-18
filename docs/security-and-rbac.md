# Security, Role-Based Access Control (RBAC), Approval and Audit

## 1. Purpose

This document describes the security-related controls implemented in the AI Incident Investigation and Remediation Agent.

It covers:

- Existing application roles
- Role declaration and authorization checks
- Incident department-access validation
- Human approval and rejection
- Corrective-action execution safeguards
- Audit events and traceability
- Current implementation boundaries

The descriptions below reflect the existing application code. They do not imply integration with an external identity provider or a production enterprise security platform.

## 2. RBAC implementation overview

The application uses role information supplied through API request models and validates selected operations in the mock enterprise API.

The three role names used in the current implementation are:

| Role | Purpose |
|---|---|
| `incident_investigator` | Represents a user requesting an incident investigation |
| `incident_approver` | Allows a reviewer to approve or reject a remediation recommendation |
| `incident_admin` | Provides administrative access for the implemented department-access and approval/action checks |

### 2.1 Where are the roles declared?

The role names are supplied through request models in:

`app/main.py`

The relevant request fields are:

- `RequesterDetails.roles`
- `ApprovalRequest.reviewer_roles`

The roles are supplied as request data. They are not defined through a centralized role enum or an external RBAC configuration service.

### 2.2 Where are the roles enforced?

Authorization checks are implemented in:

`app/tools/mock_enterprise_api.py`

The mock enterprise API validates access to incidents and restricts approval, rejection and corrective-action operations based on the supplied role information.

## 3. Incident access control

The mock enterprise API performs department-based access validation when accessing an incident.

The requester information includes:

- `user_id`
- `departments`
- `roles`

The access check is implemented in `_check_incident_access()`.

The implemented behavior includes:

1. The requester must have access to the incident's department.
2. A requester with the `incident_admin` role bypasses the department-access check.
3. Access is evaluated using the requester information supplied to the application.

**Important implementation detail:** Although `incident_investigator` is one of the role names used by the application, the described department-access check does not itself establish a separate mandatory `incident_investigator` role requirement.

## 4. Approval and rejection authorization

The application uses a human approval step before executing a corrective action.

The reviewer information is supplied through the approval request, including:

- `reviewer`
- `reviewer_roles`

The mock enterprise API checks whether the reviewer has either:

- `incident_approver`
- `incident_admin`

A reviewer without either of these roles is not authorized to perform the protected approval/rejection operation.

### Approval flow

1. The investigation workflow produces a remediation recommendation.
2. The recommendation is registered.
3. The workflow pauses for human approval.
4. An authorized reviewer submits an approval request.
5. The workflow resumes and proceeds to corrective-action execution.
6. The action result is checked and recorded.

### Rejection flow

1. An authorized reviewer submits a rejection request.
2. The recommendation is marked as rejected.
3. The corrective action is not executed.
4. The workflow proceeds to its audit-trail completion path.

The approval mechanism is implemented through the FastAPI approval/rejection endpoints and LangGraph workflow resumption.

## 5. Corrective-action execution safeguards

The application does not execute a corrective action merely because an agent recommends it.

The implementation includes the following safeguards:

### 5.1 Human approval

The workflow requires an approval decision before entering the corrective-action execution path.

### 5.2 Reviewer authorization

The mock enterprise API checks for `incident_approver` or `incident_admin` before allowing the protected operation.

### 5.3 Allowlisted actions

The mock enterprise API restricts corrective actions to the following supported action names:

- `increase_db_connection_pool`
- `restart_application_instance`
- `rollback_deployment`
- `enable_read_only_mode`

This prevents the demo workflow from accepting arbitrary action names as executable corrective actions.

### 5.4 Idempotency

The implementation uses an idempotency key constructed from:

`incident_id:recommendation_id`

This helps prevent duplicate execution of the same recommendation in the mock enterprise API.

### 5.5 Action-status verification

After execution, the workflow calls the action-status verification operation using the idempotency key.

The workflow records the result as:

- `VERIFIED_SUCCESS` when the action status is `SUCCEEDED`
- `VERIFICATION_FAILED` otherwise

**Important:** These actions execute against the project's mock enterprise API. They do not restart a real application, modify a production database or roll back a real deployment.

## 6. Audit trail

The application records audit events through its audit-related components and mock enterprise API.

The implemented event types include:

| Audit event | Purpose |
|---|---|
| `INCIDENT_READ` | Records incident retrieval |
| `SERVICE_HEALTH_CHECK` | Records service-health checking |
| `RECOMMENDATION_CREATED` | Records recommendation creation |
| `RECOMMENDATION_APPROVED` | Records approval |
| `RECOMMENDATION_REJECTED` | Records rejection |
| `CORRECTIVE_ACTION_EXECUTED` | Records corrective-action execution |
| `ACTION_STATUS_VERIFIED` | Records action-status verification |

The audit endpoint is:

`GET /incidents/{incident_id}/audit`

This allows the demo application to retrieve audit information associated with an incident.

The audit implementation supports traceability of the important investigation, approval and remediation stages.

## 7. Security-related component locations

| Component | File / location | Responsibility |
|---|---|---|
| Requester and reviewer models | `app/main.py` | Accept requester and reviewer details, including role information |
| API endpoints | `app/main.py` | Expose investigation, approval, rejection and audit operations |
| Access validation | `app/tools/mock_enterprise_api.py` | Validate department access and administrative bypass |
| Approval/rejection authorization | `app/tools/mock_enterprise_api.py` | Check approver or administrator roles |
| Corrective-action authorization | `app/tools/mock_enterprise_api.py` | Restrict protected execution operations |
| Workflow approval control | `app/workflows/incident_workflow.py` | Pause for human approval and resume based on the decision |
| Audit operations | Mock enterprise API and audit-related components | Record and retrieve workflow audit events |

## 8. Current implementation boundaries

The following distinctions are important when explaining the project's security architecture.

### Implemented

- Three role names: `incident_investigator`, `incident_approver` and `incident_admin`.
- Request-based requester and reviewer role information.
- Department-based incident-access validation.
- Administrative bypass for the department-access check.
- Role checks for approval, rejection and corrective-action execution.
- Human approval before corrective-action execution.
- Allowlisted corrective-action names.
- Idempotency key for corrective-action execution.
- Action-status verification.
- Audit-event recording and retrieval.

### Not implemented as part of the current project

- External identity-provider integration.
- Entra ID authentication or token validation.
- Centralized enterprise role management.
- Production identity provisioning and lifecycle management.
- Production-grade distributed audit storage.
- Execution against real enterprise infrastructure.

The current role information is supplied through application requests. It should therefore be described as a demonstration-level authorization implementation, not as proof of authenticated enterprise identity.

The mock enterprise API also maintains mock application state; it should not be presented as a durable production security or audit service.

## 9. Interview explanation

**Question: How have you implemented RBAC in this project?**

Answer:

"In this project, I implemented a lightweight RBAC mechanism in the mock enterprise API. We use three roles: incident investigator, incident approver and incident admin.

Requester and reviewer role information is supplied through the FastAPI request models. The mock enterprise API performs department-based incident-access validation, with an administrative bypass for incident admins.

For sensitive operations such as approving or rejecting recommendations and executing corrective actions, the API checks for the incident approver or incident admin role.

I have also implemented a human approval gate, an allowlist of supported corrective actions, idempotency for execution and action-status verification. The workflow records audit events for important stages.

This is currently a demonstration-level authorization implementation. It does not yet integrate with an enterprise identity provider such as Microsoft Entra ID."

**Question: Why do you call it demonstration-level RBAC?**

Answer:

"Because the role information is supplied through API request data. The current implementation validates the supplied roles, but it does not authenticate the user's identity through an external identity provider or validate enterprise-issued access tokens. I would distinguish the authorization checks implemented in this project from a complete enterprise identity and access-management solution."

## 10. Code-review checklist

During the code walkthrough, be prepared to locate and explain:

- [ ] `RequesterDetails` and its `roles` field in `app/main.py`
- [ ] `ApprovalRequest` and its `reviewer_roles` field in `app/main.py`
- [ ] `_check_incident_access()` in `app/tools/mock_enterprise_api.py`
- [ ] Approval and rejection authorization checks
- [ ] Corrective-action allowlist
- [ ] Idempotency-key construction
- [ ] Action execution and status verification
- [ ] Approval pause and workflow resumption in `app/workflows/incident_workflow.py`
- [ ] Audit-event creation and retrieval

## 11. Conclusion

The project demonstrates a controlled incident-remediation workflow in which specialist agents investigate incidents and recommend corrective actions, while a human reviewer must authorize execution.

Role checks, department-access validation, action allowlisting, idempotency, action verification and audit-event recording provide the security-related controls implemented in the current demonstration.

The implementation boundaries are documented explicitly to distinguish the existing application from a fully integrated enterprise security platform.