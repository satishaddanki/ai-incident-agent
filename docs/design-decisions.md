# Design Decisions and Technical Rationale

## 1. Purpose

This document explains the key technical and architectural decisions made while developing the AI Incident Investigation and Remediation Agent.

It covers the reasoning behind the selected technologies, workflow design, multi-agent orchestration, knowledge retrieval, approval mechanism and mock enterprise integration.

The explanations describe the current implementation and its intended demonstration scope.

## 2. Why a multi-agent architecture?

### Design decision

The incident investigation process is divided into specialist investigation responsibilities:

- Database investigation
- Application investigation
- Infrastructure investigation

A supervisor coordinates the investigation, and the results are collected for further analysis.

### Why this approach?

An enterprise incident can involve multiple technical domains. A single LLM prompt handling every domain may produce less structured and less focused investigation results.

Separating the investigation responsibilities provides:

- Domain-specific investigation instructions.
- Independent findings from different technical perspectives.
- Parallel execution of specialist investigations.
- Structured outputs that can be consolidated.
- A clearer separation of responsibilities.

### Current implementation

The supervisor and specialist orchestration are implemented in:

- `app/workflows/incident_workflow.py`
- `app/workflows/parallel_workflow.py`
- `app/agents/specialist_agents.py`

The three specialist investigations are coordinated through the parallel workflow.

### Trade-off

A multi-agent architecture introduces orchestration complexity, additional LLM calls and potentially higher execution time or resource consumption.

It is justified here because the project demonstrates investigation across multiple technical domains.

## 3. Why LangGraph?

### Design decision

LangGraph is used to model and execute the investigation and remediation workflow.

### Why this approach?

The application is not simply a linear chatbot interaction. It needs to coordinate multiple stages, maintain workflow state, execute parallel tasks and pause for human approval.

LangGraph provides:

- Explicit workflow nodes and edges.
- Shared workflow state.
- Conditional execution paths.
- Parallel execution patterns.
- Checkpointing.
- Pause and resume behavior through interrupts and commands.

### Current implementation

The primary workflow is defined in:

`app/workflows/incident_workflow.py`

The parallel specialist workflow is defined in:

`app/workflows/parallel_workflow.py`

The application uses `MemorySaver` for workflow checkpointing and resumes the approval flow using LangGraph's command-based resume mechanism.

### Trade-off

LangGraph introduces a learning and maintenance overhead compared with a simple sequential Python function.

However, explicit graph orchestration makes the investigation, approval and remediation stages easier to understand and control.

The current `MemorySaver` implementation is suitable for the demonstration but is not a durable distributed production checkpoint store.

## 4. Why parallel specialist investigation?

### Design decision

Database, application and infrastructure specialists investigate the incident independently through a parallel workflow.

### Why this approach?

A single incident may have symptoms across several systems.

For example, an application slowdown could be associated with:

- Database connection exhaustion.
- Application thread or resource exhaustion.
- Infrastructure resource constraints.

Running independent investigations allows the system to gather findings from multiple domains without forcing one specialist to wait for another.

### Current implementation

The parallel graph follows this structure:

```text
START
  |
Supervisor
  |
  +----------+----------+
  |          |          |
Database  Application  Infrastructure
  |          |          |
  +----------+----------+
             |
       Collect Results
             |
            END
```

The implementation is in:

`app/workflows/parallel_workflow.py`

### Trade-off

Parallel execution can reduce investigation latency, but it does not guarantee faster execution in every situation.

It also requires result collection and conflict handling because specialists may produce overlapping or inconsistent findings.

## 5. Why Retrieval-Augmented Generation (RAG)?

### Design decision

The application retrieves relevant incident knowledge before generating specialist investigation findings.

### Why this approach?

LLMs do not automatically know the specific historical incident records and operational knowledge maintained by an organization.

RAG provides relevant contextual information to the model at investigation time.

This helps the specialist agents ground their reasoning in available knowledge rather than relying entirely on general model knowledge.

### Current implementation

The RAG components are implemented in:

- `app/rag/ingestion.py`
- `app/rag/retriever.py`
- `app/rag/resolved_ingestion.py`

The current knowledge source is JSON-based incident knowledge.

The retrieval process uses:

- Ollama embeddings.
- Qdrant vector storage.
- Similarity-based retrieval.
- Retrieved context supplied to the specialist investigation process.

The configured Qdrant collection is:

`incident_knowledge`

The embedding dimension is 768.

The specialist investigation retrieves up to three relevant chunks per domain.

### Trade-off

RAG introduces ingestion, chunking, embedding and retrieval dependencies.

The quality of the investigation depends on the quality of the source knowledge and relevance of retrieved chunks.

RAG reduces dependence on unsupported model assumptions, but it does not guarantee that every generated conclusion is correct.

## 6. Why Ollama and local models?

### Design decision

The application uses Ollama to access locally hosted models.

The current model configuration includes:

| Purpose | Model |
|---|---|
| LLM generation | `qwen2.5:7b` |
| Embeddings | `nomic-embed-text:latest` |

### Why this approach?

Local inference provides a practical way to demonstrate LLM-based investigation without depending on a hosted commercial LLM API.

It also provides greater control over the model runtime and allows the project to be exercised in a local development environment.

### Current implementation

The custom Ollama client is implemented in:

`app/core/ollama_client.py`

The configuration is maintained through the application's configuration components.

### Trade-off

Local inference depends on available CPU, GPU and memory resources.

Performance and model quality may differ from hosted, larger-scale models.

The application therefore depends on Ollama being available and the configured models being present.

## 7. Why Qdrant?

### Design decision

Qdrant is used as the vector database for incident knowledge retrieval.

### Why this approach?

The application needs to store and retrieve vector representations of incident knowledge.

Qdrant supports vector storage and similarity search, making it suitable for the current RAG implementation.

### Current implementation

Qdrant client operations are implemented in:

- `app/rag/ingestion.py`
- `app/rag/retriever.py`
- `app/rag/resolved_ingestion.py`

The collection used by the application is:

`incident_knowledge`

The configured vector dimension is 768.

### Trade-off

Qdrant introduces a separate vector-storage dependency that must be available and correctly configured.

The current implementation uses Qdrant for vector retrieval; it should not be described as a complete enterprise knowledge-management platform.

## 8. Why a conflict-resolution stage?

### Design decision

The system collects findings from the specialist agents and processes them through a conflict-resolution stage before remediation recommendation generation.

### Why this approach?

Independent agents may produce:

- Duplicate evidence.
- Overlapping root-cause hypotheses.
- Different confidence levels.
- Inconsistent or unverified conclusions.

Passing all findings directly into remediation could result in an unclear or poorly supported recommendation.

A consolidation stage provides an opportunity to organize findings and identify inconsistencies.

### Current implementation

The conflict-resolution logic is implemented in:

`app/agents/conflict_resolver.py`

The workflow also uses the RCA-related component:

`app/agents/rca_agent.py`

### Trade-off

Conflict resolution does not guarantee that the final root cause is correct.

The quality of the consolidated result still depends on specialist findings, retrieved evidence and LLM output.

## 9. Why a separate remediation agent?

### Design decision

The remediation recommendation is generated through a separate remediation component rather than allowing each specialist to execute corrective actions independently.

### Why this approach?

Investigation and remediation are different responsibilities.

Specialists focus on identifying possible causes and providing evidence. The remediation stage uses the consolidated findings to formulate a recommendation.

This separation helps maintain a controlled progression from investigation to proposed action.

### Current implementation

The remediation component is implemented in:

`app/agents/remediation_agent.py`

The recommendation is registered through the mock enterprise API before the approval stage.

### Trade-off

A separate remediation stage introduces another workflow step and additional model processing.

It provides clearer responsibility separation, but the recommendation still requires validation and human review.

## 10. Why human-in-the-loop approval?

### Design decision

The workflow requires human approval before corrective-action execution.

### Why this approach?

Incident remediation can affect application availability, database operations and infrastructure stability.

Allowing an AI agent to execute every suggested action automatically would introduce operational risk.

Human approval provides a control point where an authorized reviewer can evaluate and approve or reject a recommendation.

### Current implementation

The approval stage is implemented in:

`app/workflows/incident_workflow.py`

The FastAPI approval and rejection endpoints are implemented in:

`app/main.py`

The mock enterprise API performs the relevant reviewer authorization checks.

The workflow resumes after the approval decision.

### Trade-off

Human approval introduces a waiting period and requires reviewer availability.

For this project, that trade-off is intentional: controlled remediation is more important than fully autonomous execution.

## 11. Why a mock enterprise API?

### Design decision

The application uses a mock enterprise API to represent incident management, service-health, recommendation registration, corrective-action execution and audit operations.

### Why this approach?

The project needs to demonstrate the interaction between AI-driven investigation and enterprise operational systems without connecting to real production infrastructure.

A mock API allows the workflow to demonstrate these interactions in a controlled local environment.

### Current implementation

The mock enterprise API is implemented in:

`app/tools/mock_enterprise_api.py`

It supports the application's required enterprise operations and maintains mock state in memory.

### Trade-off

The mock implementation makes the project easier to run and demonstrate, but it does not provide real enterprise integration or durable production state.

## 12. Why FastAPI?

### Design decision

FastAPI exposes the incident investigation and workflow-control operations through REST endpoints.

### Why this approach?

The application needs an API layer that can:

- Accept incident investigation requests.
- Expose application health.
- Retrieve workflow status.
- Receive approval or rejection decisions.
- Retrieve incident audit events.

FastAPI also supports request validation through Pydantic models.

### Current implementation

The API application is implemented in:

`app/main.py`

The implemented endpoints include:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Application health |
| POST | `/incidents/investigate` | Start an investigation |
| GET | `/incidents/{thread_id}/status` | Retrieve workflow status |
| POST | `/incidents/{thread_id}/approve` | Submit approval |
| POST | `/incidents/{thread_id}/reject` | Submit rejection |
| GET | `/incidents/{incident_id}/audit` | Retrieve audit events |

## 13. Why Docker?

### Design decision

Docker is used to package and run the application in a container.

### Why this approach?

Containerization provides a repeatable application runtime and reduces differences between development and deployment environments.

It also supports local validation of the packaged FastAPI application.

### Current implementation

The project includes:

- `Dockerfile`
- `docker-compose.yml`

The Docker image was built and the application was successfully started in a local container during validation.

The container health endpoint was checked successfully.

### Trade-off

Containerization does not by itself provide production orchestration, high availability, autoscaling or distributed persistence.

Those capabilities are outside the current implementation scope.

## 14. Why GitHub Actions?

### Design decision

GitHub Actions is used to define an automated CI workflow.

### Why this approach?

Automated validation helps detect application and test issues when changes are committed.

It provides a repeatable pipeline for executing the project's automated tests.

### Current implementation

The CI workflow is maintained under:

`.github/workflows/`

The pipeline includes a pytest execution step.

The latest CI status must be checked before claiming that the pipeline is consistently passing.

## 15. Summary of design decisions

| Design area | Current choice | Primary reason |
|---|---|---|
| API framework | FastAPI | REST API and request validation |
| Workflow orchestration | LangGraph | Stateful, conditional and resumable workflows |
| Agent architecture | Supervisor and specialist agents | Domain-specific investigation |
| Parallel execution | LangGraph parallel workflow | Independent specialist investigations |
| Knowledge retrieval | RAG | Ground findings in incident knowledge |
| Vector database | Qdrant | Similarity-based vector retrieval |
| LLM runtime | Ollama | Local model inference |
| LLM | Qwen 2.5 7B | Investigation and recommendation generation |
| Embeddings | Nomic Embed Text | Vector representation of knowledge |
| Conflict handling | Conflict resolver and RCA components | Consolidate specialist findings |
| Remediation | Separate remediation component | Separate investigation from proposed action |
| Approval | Human-in-the-loop | Control corrective-action execution |
| Enterprise integration | Mock enterprise API | Demonstrate operational interactions safely |
| Packaging | Docker | Consistent local application runtime |
| CI | GitHub Actions | Automated test execution |

## 16. Architect-level interview questions

### Q1. Why did you choose LangGraph instead of a simple LangChain chain?

The workflow needs state management, parallel specialist execution, conditional transitions and human approval with pause/resume behavior. LangGraph provides explicit graph-based orchestration for these requirements. A simple sequential chain would require additional custom logic to coordinate these workflow stages.

### Q2. Why use multiple agents instead of one powerful LLM?

The investigation spans database, application and infrastructure domains. Specialist agents provide domain-focused analysis and independent findings. Their results are consolidated before a remediation recommendation is created. This provides separation of responsibilities, although it introduces additional orchestration and model-call overhead.

### Q3. How do you handle conflicting agent findings?

The workflow collects the specialist findings and passes them through the conflict-resolution and RCA components. The intention is to consolidate evidence, identify inconsistencies and produce a more structured analysis before remediation. The resolver does not guarantee that every conclusion is correct, so evidence validation remains important.

### Q4. Why use RAG instead of sending the entire knowledge base to the LLM?

RAG retrieves relevant knowledge chunks for the current investigation rather than sending the complete knowledge base. This keeps the context focused and makes the approach more scalable as the knowledge base grows. Retrieval quality remains dependent on the quality of the source data, chunking and embeddings.

### Q5. Why not allow agents to execute remediation automatically?

Corrective actions may affect critical systems. The application therefore separates recommendation generation from execution and requires an authorized human reviewer to approve the recommendation before the mock corrective action is executed.

### Q6. What would you improve before production deployment?

I would prioritize enterprise identity integration, durable workflow checkpointing, persistent enterprise data and audit storage, real enterprise API integration, stronger observability, operational monitoring and deployment-level resilience. These would be additional production capabilities, not features currently claimed by this implementation.

## 17. Conclusion

The architecture combines multi-agent investigation, parallel workflow orchestration, RAG-based knowledge retrieval, conflict resolution, remediation recommendation and human approval.

The design emphasizes separation of responsibilities, structured workflow control and safe demonstration of corrective-action execution.

Each technology choice supports a specific responsibility in the current implementation, while the documented trade-offs distinguish the demonstration from a production enterprise platform.