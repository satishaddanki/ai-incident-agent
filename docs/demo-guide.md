# Demo Guide — AI Incident Investigation and Remediation Agent

## 1. Demo Objective

The objective of this demonstration is to showcase an AI-powered incident investigation and controlled-remediation workflow using a multi-agent architecture.

The demonstration covers:

- Incident investigation through FastAPI.
- Supervisor-based agent orchestration.
- Parallel specialist investigations.
- RAG-based knowledge retrieval.
- Conflict resolution and root-cause analysis.
- Remediation recommendation generation.
- Human approval and rejection.
- Controlled corrective-action execution.
- Action-status verification.
- Audit-event retrieval.

The demonstration uses a mock enterprise API. No real production infrastructure is modified.

## 2. Demo Preparation

### 2.1 Prerequisites

Before starting the demonstration, ensure the following are available:

- Python virtual environment.
- Required Python packages.
- Ollama service.
- Configured Ollama LLM model.
- Configured Ollama embedding model.
- Qdrant service.
- Required JSON incident knowledge files.
- Initialized Qdrant collection.
- FastAPI application.

### 2.2 Start Ollama

Ensure Ollama is running.

Check the configured models:

```powershell
ollama list
```

Expected models:

```text
qwen2.5:7b
nomic-embed-text:latest
```

### 2.3 Start Qdrant

Start the Qdrant service using the existing project configuration.

Confirm that the configured endpoint is reachable.

### 2.4 Activate Python Environment

From the project directory:

```powershell
.venv\Scripts\Activate.ps1
```

### 2.5 Start FastAPI

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open:

```text
http://localhost:8000/docs
```

Verify:

```text
GET /health
```

Expected response:

```text
healthy
```

## 3. Recommended Demonstration Sequence

The recommended demonstration should take approximately 15–20 minutes.

| Sequence | Demonstration | Approx. time |
|---|---|---:|
| 1 | Project introduction and architecture | 2 min |
| 2 | Incident investigation request | 2 min |
| 3 | Multi-agent parallel investigation | 3 min |
| 4 | RAG and conflict resolution | 3 min |
| 5 | Remediation recommendation | 2 min |
| 6 | Human approval | 2 min |
| 7 | Corrective-action execution and verification | 2 min |
| 8 | Audit trail and conclusion | 2 min |

## 4. Step-by-Step Demonstration

### Step 1: Introduce the Application

Explain:

"I developed an AI Incident Investigation and Remediation Agent using Python, FastAPI and LangGraph.

The objective is to automate the initial investigation of enterprise incidents using specialized AI agents.

Instead of relying on a single agent, the application coordinates database, application and infrastructure specialists. Their findings are consolidated before generating a remediation recommendation.

The system also includes human approval before corrective-action execution."

Show:

- Project folder structure.
- `README.md`.
- `docs/architecture.md`.
- Architecture flow diagram.

### Step 2: Start an Incident Investigation

Open the FastAPI Swagger interface:

```text
http://localhost:8000/docs
```

Select:

```text
POST /incidents/investigate
```

Use the request schema displayed by Swagger.

Provide a valid incident identifier and requester details, including the roles and department information expected by the current request model.

Submit the request.

Explain:

"The API receives the incident investigation request and initiates the LangGraph workflow. The workflow retrieves the incident context and checks the relevant service health information before coordinating the investigation."

Show:

- Request payload.
- API response.
- Returned workflow/thread identifier.

Use the actual response fields from the running application during the presentation.

### Step 3: Demonstrate Supervisor and Specialist Agents

Open:

`app/workflows/incident_workflow.py`

Explain the supervisor's responsibility:

"The supervisor coordinates the incident investigation and delegates domain-specific analysis to specialist agents."

Then open:

`app/workflows/parallel_workflow.py`

Explain:

"We have three specialist investigation areas: database, application and infrastructure.

These investigations are executed through a parallel workflow. Each specialist examines the available incident context and produces findings relevant to its domain.

The results are subsequently collected for consolidation."

Show the relevant specialist implementations in:

`app/agents/specialist_agents.py`

The expected conceptual flow is:

```text
Supervisor
    |
    +-------------------+
    |         |         |
    v         v         v
 Database  Application Infrastructure
 Specialist Specialist  Specialist
    |         |         |
    +---------+---------+
              |
        Collect Findings
```

### Step 4: Explain RAG and Knowledge Retrieval

Open:

- `app/rag/ingestion.py`
- `app/rag/retriever.py`
- `app/rag/resolved_ingestion.py`

Explain:

"The application uses Retrieval-Augmented Generation to provide relevant incident knowledge to the specialist agents.

The current knowledge source consists of JSON-based incident knowledge records.

During ingestion, the application prepares the knowledge for embedding and stores vector representations in Qdrant.

At investigation time, relevant knowledge is retrieved and supplied as contextual information to support the specialist analysis."

Show:

- JSON knowledge source.
- Ingestion implementation.
- Retriever implementation.
- Qdrant collection configuration.

Do not claim PDF ingestion. The current implementation uses JSON-based knowledge.

### Step 5: Demonstrate Conflict Resolution and Root-Cause Analysis

Open:

- `app/agents/conflict_resolver.py`
- `app/agents/rca_agent.py`

Explain:

"Independent specialists may produce overlapping findings or different root-cause hypotheses.

The conflict-resolution stage consolidates the investigation findings, and the RCA component processes the available evidence to support root-cause analysis.

This provides a structured investigation result before the remediation recommendation is generated."

Show the relevant workflow nodes and their connections in:

`app/workflows/incident_workflow.py`

### Step 6: Demonstrate Remediation Recommendation

Open:

`app/agents/remediation_agent.py`

Explain:

"Once the investigation findings have been consolidated, the remediation component generates a proposed corrective action.

The recommendation is registered through the mock enterprise API.

Importantly, generating a recommendation does not automatically execute it."

Show the recommendation registration and corresponding workflow node.

### Step 7: Demonstrate Human Approval

This is one of the most important parts of the demonstration.

Show the pending-approval state.

Previously observed output included:

```text
HUMAN APPROVAL REQUIRED

Human approval is required before remediation.

recommendation_status: PENDING_APPROVAL
execution_status: NOT_EXECUTED
```

Explain:

"The workflow pauses at this point using LangGraph's human-in-the-loop interrupt mechanism.

An authorized reviewer must approve or reject the recommendation.

This prevents the AI agent from independently executing a corrective action without human authorization."

Show:

- Approval request model in `app/main.py`.
- Approval endpoint.
- Approval-related workflow node.
- Reviewer authorization check in `app/tools/mock_enterprise_api.py`.

### Step 8: Demonstrate Approval and Corrective-Action Execution

Submit an approval request using:

```text
POST /incidents/{thread_id}/approve
```

Use the actual request schema shown in Swagger.

Explain:

"After receiving an authorized approval decision, the application resumes the paused workflow.

The approved corrective action is submitted to the mock enterprise API.

The implementation uses an idempotency key based on the incident ID and recommendation ID to help prevent duplicate execution."

Show:

`app/tools/mock_enterprise_api.py`

Explain that the corrective-action implementation is simulated and does not modify real infrastructure.

### Step 9: Demonstrate Action-Status Verification

Explain:

"After submitting the corrective action, the workflow checks its execution status through the mock enterprise API.

The workflow records whether the action was verified successfully or whether verification failed."

Show the relevant status-verification node in:

`app/workflows/incident_workflow.py`

The two verification outcomes are:

- `VERIFIED_SUCCESS`
- `VERIFICATION_FAILED`

### Step 10: Demonstrate Audit Trail

Use:

```text
GET /incidents/{incident_id}/audit
```

Explain:

"The application records important events throughout the investigation and remediation lifecycle.

This provides traceability of incident retrieval, investigation, recommendation generation, approval or rejection, corrective-action execution and verification."

Show the audit-related implementation in:

`app/tools/mock_enterprise_api.py`

Conclude:

"This completes the incident investigation and controlled-remediation workflow."

## 5. Optional Demonstration: Rejection Path

If sufficient time is available, demonstrate the rejection path.

Submit a rejection request through:

```text
POST /incidents/{thread_id}/reject
```

Use an authorized reviewer and the exact request schema displayed in Swagger.

Explain:

"If the reviewer rejects the recommendation, the workflow records the rejection and does not proceed with corrective-action execution."

Show the resulting recommendation status and relevant audit events.

This demonstrates that the application supports both approval and rejection decisions.

## 6. Important Source-Code Walkthrough

The following files should be kept ready for the technical discussion.

| File | What to explain |
|---|---|
| `app/main.py` | FastAPI endpoints and request models |
| `app/workflows/incident_workflow.py` | Main orchestration, approval interrupt and workflow resumption |
| `app/workflows/parallel_workflow.py` | Parallel specialist execution |
| `app/agents/specialist_agents.py` | Specialist responsibilities |
| `app/agents/conflict_resolver.py` | Consolidation and conflict handling |
| `app/agents/rca_agent.py` | Root-cause analysis |
| `app/agents/remediation_agent.py` | Remediation recommendation |
| `app/rag/ingestion.py` | Knowledge ingestion |
| `app/rag/retriever.py` | Knowledge retrieval |
| `app/tools/mock_enterprise_api.py` | Mock enterprise operations, authorization and audit |
| `app/core/ollama_client.py` | Local LLM and embedding interaction |
| `app/core/config.py` | Application configuration |

## 7. Potential Interview Questions During the Demo

### Q1. Why did you use LangGraph?

LangGraph provides stateful workflow orchestration, conditional transitions, parallel execution and human-in-the-loop pause/resume functionality. These capabilities fit an incident investigation and controlled-remediation workflow.

### Q2. Where are the agents implemented?

The specialist agents are implemented in `app/agents/specialist_agents.py`. Their execution is coordinated through the workflow definitions in `app/workflows/incident_workflow.py` and `app/workflows/parallel_workflow.py`.

### Q3. How do agents communicate?

The workflow coordinates them through shared LangGraph state and the parallel execution structure. Specialist outputs are collected and passed to subsequent workflow stages.

### Q4. How do you prevent conflicting agent recommendations?

The application uses a conflict-resolution stage to consolidate specialist findings before root-cause analysis and remediation recommendation generation.

### Q5. How does RAG work in this application?

Incident knowledge is ingested, converted into embeddings using the configured Ollama embedding model and stored in Qdrant. During investigation, relevant knowledge is retrieved and supplied to the specialist agents.

### Q6. How do you prevent unauthorized remediation?

The application validates reviewer roles in the mock enterprise API and requires an authorized approval decision before the corrective-action execution path proceeds.

### Q7. What happens if the reviewer rejects the recommendation?

The rejection is recorded, and the workflow does not proceed with corrective-action execution.

### Q8. What happens if corrective-action verification fails?

The workflow records `VERIFICATION_FAILED` rather than reporting successful verification. The mock API's returned action status determines the verification result.

### Q9. Is this connected to a real enterprise incident-management system?

No. The current project uses a mock enterprise API to demonstrate the integration points and controlled workflow. Real enterprise integration is a future production extension.

### Q10. How would you scale this architecture?

I would introduce durable workflow checkpointing, persistent enterprise data, scalable vector infrastructure, asynchronous task execution, distributed observability and enterprise identity integration. I would also evaluate agent concurrency, model-serving capacity, retrieval latency and cost.

## 8. Demo Contingency Plan

If the application or an external dependency is unavailable during the assignment call, follow this priority order:

1. Explain the architecture using `docs/architecture.md`.
2. Show the main workflow in `app/workflows/incident_workflow.py`.
3. Show parallel execution in `app/workflows/parallel_workflow.py`.
4. Explain RAG using the ingestion and retrieval components.
5. Show the approval interrupt and resume implementation.
6. Explain the mock corrective-action execution and audit implementation.
7. Present previously captured execution evidence, clearly identifying it as previously observed output.

Do not present old execution output as a live execution.

## 9. Final Project Presentation

Suggested closing statement:

"This project demonstrates how agentic AI can support enterprise incident investigation and controlled remediation.

I designed the solution around a supervisor-coordinated multi-agent architecture, with independent database, application and infrastructure specialists.

The system uses RAG to retrieve relevant historical incident knowledge, consolidates specialist findings through conflict resolution and root-cause analysis, and generates a remediation recommendation.

A key design principle is controlled autonomy. The AI system can investigate and recommend, but an authorized human must approve the proposed corrective action before execution.

The current implementation demonstrates this end-to-end workflow through FastAPI, LangGraph, Ollama and Qdrant, with a mock enterprise API for operational interactions.

The architecture provides a foundation for future integration with real enterprise incident-management and infrastructure systems."

## 10. Final Demonstration Checklist

### Before the call

- [ ] Confirm Ollama is running.
- [ ] Confirm the configured models are available.
- [ ] Confirm Qdrant is running.
- [ ] Confirm the knowledge collection is available.
- [ ] Start FastAPI.
- [ ] Check `/health`.
- [ ] Open Swagger documentation.
- [ ] Keep the project source code open in the editor.
- [ ] Keep architecture and component-interaction diagrams ready.
- [ ] Keep the previously observed approval output available.

### During the call

- [ ] Introduce the project and business problem.
- [ ] Explain the architecture.
- [ ] Start an incident investigation.
- [ ] Explain supervisor coordination.
- [ ] Show parallel specialist execution.
- [ ] Explain RAG retrieval.
- [ ] Show conflict resolution and RCA.
- [ ] Show recommendation generation.
- [ ] Demonstrate pending human approval.
- [ ] Approve the recommendation.
- [ ] Show corrective-action execution and verification.
- [ ] Retrieve the audit trail.
- [ ] Explain implementation limitations honestly.

### After the demonstration

- [ ] Explain the most important design decisions.
- [ ] Discuss production-readiness improvements.
- [ ] Answer technical questions using the actual source code.

---

## 11. Key Takeaway

The most important aspect of this project is not simply generating an AI recommendation.

It is demonstrating a complete, controlled incident-management workflow in which multiple AI agents investigate independently, consolidate their findings, recommend corrective actions and operate within a human-approval and audit-controlled process.