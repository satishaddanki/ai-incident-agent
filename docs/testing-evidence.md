# Testing Evidence and Known Limitations

## 1. Purpose

This document summarizes the testing approach, observed execution evidence and known implementation limitations of the AI Incident Investigation and Remediation Agent.

The objective is to explain what has been tested and demonstrated, without claiming test coverage or production capabilities that have not been verified.

## 2. Testing approach

The project uses `pytest` for automated testing.

The tests validate application components and workflow behavior, including:

- Incident investigation logic
- Specialist-agent behavior
- Parallel investigation workflow
- Knowledge retrieval and evidence handling
- Conflict resolution and remediation recommendation
- Approval and rejection behavior
- Corrective-action execution and verification
- API behavior and error handling

The exact coverage depends on the test cases currently present in the `tests/` directory.

## 3. Test execution

### 3.1 Run the automated test suite

Activate the project's virtual environment and execute:

```powershell
pytest -v
```

This runs the available automated tests and displays individual test results.

### 3.2 Run tests with a summary

```powershell
pytest -v --tb=short
```

This displays concise failure tracebacks if a test fails.

### 3.3 Dependency consistency check

```powershell
python -m pip check
```

Observed result during dependency review:

```text
No broken requirements found.
```

This confirms that pip did not report broken installed package requirements at the time of that check. It is not a substitute for application testing.

## 4. Functional workflow evidence

The application has been exercised through its incident investigation and remediation workflow.

The demonstrated workflow includes:

1. Incident retrieval.
2. Service-health checking.
3. Supervisor-based investigation coordination.
4. Parallel database, application and infrastructure investigation.
5. Collection of specialist findings.
6. Conflict resolution and root-cause analysis.
7. Remediation recommendation generation.
8. Recommendation registration.
9. Human approval or rejection.
10. Corrective-action execution after approval.
11. Action-status verification.
12. Audit-trail completion.

The execution flow is implemented in:

`app/workflows/incident_workflow.py`

The parallel specialist workflow is implemented in:

`app/workflows/parallel_workflow.py`

## 5. Human approval test evidence

An observed execution demonstrated the pending-approval state.

The output included:

```text
Human approval is required before remediation.
recommendation_status: PENDING_APPROVAL
execution_status: NOT_EXECUTED
```

This demonstrates that the workflow can reach the approval stage without immediately executing the corrective action.

The approved and rejected paths are handled through the approval/rejection endpoints and LangGraph workflow resumption.

## 6. Corrective-action execution and verification

The approved workflow proceeds to the mock corrective-action execution operation.

The application uses an idempotency key based on:

```text
incident_id:recommendation_id
```

After execution, it queries the mock enterprise API for the action status.

The workflow distinguishes:

- `VERIFIED_SUCCESS`
- `VERIFICATION_FAILED`

These statuses represent the result of the application's verification logic against the mock enterprise API. They do not establish that an actual production infrastructure change occurred.

## 7. API and container validation

The FastAPI application was successfully launched in a local Docker container during the implementation process.

The container was run with the following port mapping:

```text
8001:8000
```

The health endpoint was checked:

```text
http://localhost:8001/health
```

Observed response:

```text
healthy
```

This confirms that the containerized application started and its health endpoint responded successfully during that validation.

It does not by itself prove that every API endpoint or complete workflow works in a production deployment.

## 8. CI/CD validation status

A GitHub Actions CI workflow was created to automate application validation.

The pipeline includes a test execution step using:

```text
pytest -v
```

A CI run previously reported a test failure. Therefore, the pipeline should not be described as consistently passing unless the latest GitHub Actions run has been checked.

The current status of the latest CI run should be verified before the assignment demonstration.

## 9. Known limitations

The following limitations should be communicated transparently.

### 9.1 Mock enterprise integration

Enterprise incident, service-health, recommendation, corrective-action and audit operations are represented through the mock enterprise API.

The project does not execute actual infrastructure remediation.

### 9.2 In-memory application state

The mock enterprise API maintains application state in memory. This is suitable for demonstrating the workflow but is not a durable distributed enterprise persistence mechanism.

### 9.3 Workflow checkpoint persistence

The current workflow uses LangGraph `MemorySaver` for checkpointing.

This supports workflow pause and resume in the current application process, but it should not be presented as durable, distributed production checkpoint storage.

### 9.4 Local LLM dependency

The application uses a locally hosted Ollama model for LLM operations.

Model availability, inference speed and resource consumption depend on the local environment.

### 9.5 JSON-based knowledge ingestion

The current knowledge base uses JSON-based incident knowledge files.

PDF ingestion should not be presented as an implemented project capability.

### 9.6 Demonstration-level authorization

The project implements role checks using requester and reviewer information supplied through application requests.

It does not currently integrate with an external identity provider or validate enterprise-issued authentication tokens.

### 9.7 Retrieval and reasoning limitations

The quality of investigation findings depends on the available knowledge data, retrieved evidence and LLM-generated analysis.

Agent-generated root-cause hypotheses and recommendations should be treated as decision-support outputs, not as guaranteed facts.

### 9.8 Production operational controls

The current project should not be described as a fully production-hardened enterprise remediation platform. Production deployment would require additional identity, persistence, observability, infrastructure integration and operational controls.

## 10. Evidence to verify before the assignment call

Use this checklist to confirm the latest state before presenting the project.

- [ ] Run `pytest -v` and capture the latest result.
- [ ] Confirm the latest GitHub Actions workflow status.
- [ ] Start the application or Docker container.
- [ ] Verify `GET /health`.
- [ ] Execute one incident investigation.
- [ ] Confirm the recommendation reaches `PENDING_APPROVAL`.
- [ ] Verify that no action is executed before approval.
- [ ] Approve the recommendation using an authorized reviewer.
- [ ] Verify the mock action status.
- [ ] Retrieve the incident audit events.
- [ ] If time permits, demonstrate the rejection path and confirm no corrective action is executed.

Do not spend time rerunning every test if the assignment team schedules the call unexpectedly. Prioritize the health check and one successful end-to-end demonstration.

## 11. Interview explanation

**Question: How did you test this application?**

Answer:

"I used pytest for automated testing of the application components and workflow behavior. I also validated the FastAPI application locally and successfully ran it in Docker, where I checked the health endpoint.

For the end-to-end workflow, I validated incident retrieval, parallel specialist investigation, recommendation generation and the human approval stage. I also exercised the mock corrective-action execution and status-verification flow.

One important design decision is that the workflow does not execute a remediation action before human approval. The current enterprise operations are mocked, so I clearly distinguish workflow validation from real production infrastructure remediation."

**Question: Is the application production-ready?**

Answer:

"The project demonstrates the core investigation and controlled-remediation workflow. However, the current implementation uses a mock enterprise API, in-memory mock state, local Ollama inference and MemorySaver checkpointing. Before production deployment, I would strengthen identity integration, durable persistence, observability, enterprise API integration and operational security controls."

## 12. Conclusion

The project demonstrates an end-to-end incident investigation and controlled-remediation workflow with parallel specialist agents, knowledge retrieval, human approval, mock corrective-action execution, status verification and audit-event recording.

Testing and deployment evidence should be presented according to the latest verified results. Known limitations are explicitly documented to distinguish the current implementation from a production enterprise platform.