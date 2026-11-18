# AI Incident Investigation and Remediation Agent

An AI-powered incident investigation and controlled-remediation application built using Python, FastAPI, LangGraph, Ollama, Qdrant and a multi-agent architecture.

The application investigates enterprise-style incidents using specialized agents for database, application and infrastructure domains. It retrieves relevant incident knowledge, consolidates investigation findings, generates remediation recommendations and requires human approval before executing a corrective action through a mock enterprise API.

---

## 1. Project Overview

Enterprise incidents often involve multiple technical domains. Investigating them manually can require engineers to examine application logs, database conditions, infrastructure health and historical incident records.

This project demonstrates an AI-driven incident investigation workflow that coordinates multiple specialist agents and generates structured remediation recommendations.

The application follows a controlled workflow:

1. Receive an incident investigation request.
2. Retrieve incident information and check service health.
3. Coordinate specialist agents through a supervisor.
4. Investigate database, application and infrastructure domains in parallel.
5. Collect and consolidate specialist findings.
6. Perform conflict resolution and root-cause analysis.
7. Generate a remediation recommendation.
8. Register the recommendation.
9. Pause for human approval.
10. Execute an approved corrective action through a mock enterprise API.
11. Verify the action status.
12. Record audit events.

**Important:** This is a demonstration implementation. Enterprise operations are represented by a mock API; corrective actions do not modify real production infrastructure.

## 2. Key Features

- **Multi-agent investigation:** Database, application and infrastructure specialist agents.
- **Supervisor orchestration:** Coordinates the specialist investigation workflow.
- **Parallel execution:** Runs independent specialist investigations through LangGraph.
- **Retrieval-Augmented Generation (RAG):** Retrieves relevant incident knowledge from a JSON-based knowledge base.
- **Vector search:** Uses Qdrant for similarity-based knowledge retrieval.
- **Local LLM inference:** Uses Ollama for language-model and embedding operations.
- **Conflict resolution:** Consolidates specialist findings and handles inconsistent evidence.
- **Root-cause analysis:** Processes investigation findings before remediation recommendation generation.
- **Remediation recommendation:** Generates a structured recommendation from investigation results.
- **Human-in-the-loop:** Requires an authorized reviewer to approve or reject a recommendation.
- **Corrective-action safeguards:** Uses role checks, an allowlist and idempotency for mock execution.
- **Action verification:** Checks the status returned by the mock enterprise API.
- **Audit trail:** Records important investigation, approval and remediation events.
- **REST API:** Exposes application operations through FastAPI.
- **Containerization:** Supports Docker-based application execution.
- **CI workflow:** Includes GitHub Actions automation for test execution.

## 3. Technology Stack

| Area | Technology |
|---|---|
| Programming language | Python |
| API framework | FastAPI |
| API data validation | Pydantic |
| Agent workflow orchestration | LangGraph |
| LLM runtime | Ollama |
| LLM model | Qwen 2.5 7B |
| Embedding model | Nomic Embed Text |
| Vector database | Qdrant |
| Knowledge source | JSON-based incident knowledge |
| Testing | Pytest |
| Containerization | Docker |
| CI automation | GitHub Actions |

The application uses a custom Ollama client implemented in `app/core/ollama_client.py`.

## 4. High-Level Architecture

```text
                 User / API Client
                        |
                        v
                  FastAPI Layer
                    app/main.py
                        |
                        v
                Incident Workflow
                    LangGraph
                        |
             +----------+----------+
             |                     |
             v                     v
       Incident Retrieval     Service Health
             |                     |
             +----------+----------+
                        |
                        v
                    Supervisor
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
       Database     Application   Infrastructure
       Specialist   Specialist    Specialist
          |             |             |
          +-------------+-------------+
                        |
                        v
                Collect Results
                        |
                        v
                Conflict Resolution
                        |
                        v
                  Root Cause Analysis
                        |
                        v
               Remediation Recommendation
                        |
                        v
              Recommendation Registration
                        |
                        v
                Human Approval Required
                        |
                 +------+------+
                 |             |
               Reject        Approve
                 |             |
                 v             v
              Audit       Corrective Action
                               |
                               v
                        Status Verification
                               |
                               v
                              Audit
                               |
                               v
                              END
```

### Knowledge retrieval flow

```text
JSON Knowledge Files
        |
        v
   Ingestion
        |
        v
  Text Chunking
        |
        v
 Ollama Embeddings
        |
        v
   Qdrant Vector
      Collection
        |
        v
 Similarity Retrieval
        |
        v
 Specialist Investigation
```

The current vector collection is `incident_knowledge`, configured with 768-dimensional vectors.

## 5. Project Structure

The following is the principal application structure:

```text
ai_incident_agent/
│
├── app/
│   ├── main.py
│   │
│   ├── agents/
│   │   ├── specialist_agents.py
│   │   ├── conflict_resolver.py
│   │   ├── rca_agent.py
│   │   └── remediation_agent.py
│   │
│   ├── workflows/
│   │   ├── incident_workflow.py
│   │   └── parallel_workflow.py
│   │
│   ├── rag/
│   │   ├── ingestion.py
│   │   ├── retriever.py
│   │   └── resolved_ingestion.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── ollama_client.py
│   │
│   └── tools/
│       └── mock_enterprise_api.py
│
├── tests/
│
├── docs/
│   ├── technology-stack.md
│   ├── architecture.md
│   ├── component-interaction.md
│   ├── security-and-rbac.md
│   ├── design-decisions.md
│   ├── testing-evidence.md
│   └── demo-guide.md
│
├── .github/
│   └── workflows/
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

This shows the principal components and documentation. Refer to the repository for the complete current file structure.

## 6. Prerequisites

The development environment used for this project includes:

- Python 3.12
- Ollama
- Qwen 2.5 7B model
- Nomic Embed Text model
- Qdrant
- Docker
- Git

Ensure that Ollama and Qdrant are available before running the application.

## 7. Local Setup

### Step 1: Clone the repository

```powershell
git clone <repository-url>
cd ai_incident_agent
```

Replace `<repository-url>` with the actual repository URL.

### Step 2: Create a virtual environment

```powershell
python -m venv .venv
```

### Step 3: Activate the environment

```powershell
.venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Configure application settings

Review:

`app/core/config.py`

Configure the environment variables and service connection settings expected by the current application.

Do not commit API keys, credentials or other secrets to source control.

### Step 6: Prepare Ollama models

Ensure Ollama is running and the configured models are available.

The current model configuration is:

```powershell
ollama pull qwen2.5:7b
ollama pull nomic-embed-text:latest
```

The application uses these models for LLM generation and embeddings respectively.

### Step 7: Start Qdrant

Start Qdrant using the service configuration already provided for the project.

Verify that the configured Qdrant endpoint is reachable and that the application's vector collection is available or can be initialized by the ingestion process.

### Step 8: Prepare the knowledge base

Use the existing JSON-based incident knowledge files and the project's ingestion implementation.

Relevant files:

- `app/rag/ingestion.py`
- `app/rag/resolved_ingestion.py`

Follow the current ingestion implementation and configuration when preparing the knowledge collection.

## 8. Running the Application

Start the FastAPI application from the project root:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The application should be accessible at:

```text
http://localhost:8000
```

FastAPI interactive API documentation:

```text
http://localhost:8000/docs
```

Health endpoint:

```text
http://localhost:8000/health
```

## 9. API Endpoints

The current application exposes the following endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks application health |
| POST | `/incidents/investigate` | Starts incident investigation |
| GET | `/incidents/{thread_id}/status` | Retrieves workflow status |
| POST | `/incidents/{thread_id}/approve` | Submits an approval decision |
| POST | `/incidents/{thread_id}/reject` | Submits a rejection decision |
| GET | `/incidents/{incident_id}/audit` | Retrieves incident audit events |

Use the interactive FastAPI documentation at `/docs` to inspect the current request models and test the endpoints.

## 10. Human Approval and Controlled Remediation

The application does not execute corrective actions immediately after generating a recommendation.

The workflow pauses for human approval.

The implemented reviewer roles are:

- `incident_approver`
- `incident_admin`

The mock enterprise API supports the following allowlisted corrective actions:

- `increase_db_connection_pool`
- `restart_application_instance`
- `rollback_deployment`
- `enable_read_only_mode`

After approval, the workflow executes the selected mock action and checks its status.

The workflow uses an idempotency key based on the incident and recommendation identifiers.

If the recommendation is rejected, the corrective-action execution path is not entered.

## 11. Running Automated Tests

Run the automated test suite:

```powershell
pytest -v
```

Run with concise failure output:

```powershell
pytest -v --tb=short
```

Check installed dependency consistency:

```powershell
python -m pip check
```

Refer to `docs/testing-evidence.md` for the testing approach, previously observed validation results and known limitations.

Always verify the latest local test and GitHub Actions results before reporting the current status.

## 12. Docker Execution

The project includes:

- `Dockerfile`
- `docker-compose.yml`

Build the application image:

```powershell
docker build -t ai-incident-agent:1.0.0 .
```

Run the container:

```powershell
docker run --name ai-incident-agent-local -p 8001:8000 ai-incident-agent:1.0.0
```

Check the container health endpoint:

```text
http://localhost:8001/health
```

The application was previously launched locally using this container port mapping, and the health endpoint returned `healthy`.

Note that the application container and its external dependencies, including Ollama and Qdrant, must be configured to communicate correctly in the runtime environment.

## 13. Security and Governance

The current implementation includes:

- Request-based role information.
- Department-based incident-access validation.
- Reviewer authorization checks.
- Human approval before corrective-action execution.
- Corrective-action allowlisting.
- Idempotency for mock action execution.
- Action-status verification.
- Audit-event recording.

The application currently uses demonstration-level authorization. It does not implement Microsoft Entra ID authentication or external enterprise identity-provider integration.

See:

`docs/security-and-rbac.md`

for the implementation details and boundaries.

## 14. Documentation

The `docs/` directory contains the supporting technical documentation.

| Document | Description |
|---|---|
| `technology-stack.md` | Technologies, dependencies and runtime components |
| `architecture.md` | High-level system architecture |
| `component-interaction.md` | Component responsibilities and execution flow |
| `security-and-rbac.md` | Roles, access checks, approval and audit |
| `design-decisions.md` | Technical choices and architectural trade-offs |
| `testing-evidence.md` | Testing approach, observed evidence and limitations |
| `demo-guide.md` | Planned demonstration sequence and talking points |

## 15. Known Limitations

The current project is a functional demonstration of an AI-driven investigation and controlled-remediation workflow.

Important boundaries:

- Enterprise operations use a mock API.
- Mock enterprise state is maintained in memory.
- LangGraph checkpointing uses `MemorySaver`.
- LLM inference depends on locally hosted Ollama models.
- The knowledge base uses JSON-based incident knowledge.
- Role information is supplied through API request data.
- Corrective actions do not modify real enterprise infrastructure.
- Production-grade identity integration, distributed persistence and enterprise observability are outside the current implementation.

These limitations are documented to distinguish the current application from a fully production-hardened enterprise platform.

## 16. Project Objective

The primary objective is to demonstrate how multiple specialized AI agents can collaborate to investigate technical incidents, use historical knowledge to support their analysis, consolidate findings and recommend corrective actions through a controlled human-approval workflow.

The project brings together agentic AI, RAG, workflow orchestration, API development, containerization, testing and governance concepts in one integrated application.

---

**Project:** AI Incident Investigation and Remediation Agent  
**Language:** Python  
**Orchestration:** LangGraph  
**API:** FastAPI  
**LLM Runtime:** Ollama  
**Vector Database:** Qdrant