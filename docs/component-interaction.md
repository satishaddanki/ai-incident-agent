# AI Incident Investigation and Remediation Agent
# System Architecture

## 1. Introduction

The AI Incident Investigation and Remediation Agent is an AI-powered, multi-agent system designed to investigate enterprise IT incidents, identify potential root causes, generate remediation recommendations and support controlled remediation workflows.

The application combines Python, FastAPI, LangGraph, Ollama, Qdrant and Retrieval-Augmented Generation (RAG).

The architecture uses specialized AI agents to investigate incidents across application, database and infrastructure domains. A Supervisor coordinates the investigation, while a Conflict Resolver consolidates findings before root-cause analysis and remediation recommendation generation.

Human approval is incorporated into the workflow to provide governance and prevent unauthorized remediation.

## 2. Architectural Objectives

The architecture is designed to achieve the following objectives:

- Automate incident investigation across multiple technical domains.
- Support parallel execution of specialist agents.
- Retrieve relevant historical incident knowledge through RAG.
- Consolidate findings from multiple agents.
- Generate evidence-informed root-cause analysis.
- Produce structured remediation recommendations.
- Enforce human approval before remediation proceeds.
- Maintain incident traceability and audit information.
- Provide modularity and extensibility for future enterprise integration.

## 3. High-Level System Architecture

The system consists of the following major components:

1. FastAPI application layer.
2. LangGraph orchestration engine.
3. Supervisor and specialist agents.
4. Conflict resolution and RCA components.
5. Remediation recommendation component.
6. Human approval mechanism.
7. RAG and vector database infrastructure.
8. Ollama model runtime.
9. Mock enterprise integration layer.
10. Audit and status management.

### Architecture Flow

API Consumer  
↓  
FastAPI  
↓  
LangGraph Workflow  
↓  
Supervisor  
↓  
Parallel Specialist Agents  
- Application Specialist
- Database Specialist
- Infrastructure Specialist  
↓  
Conflict Resolver  
↓  
Root Cause Analysis  
↓  
Remediation Agent  
↓  
Human Approval  
↓  
Controlled Remediation Lifecycle  
↓  
Status Verification and Audit

Supporting infrastructure includes Ollama, Qdrant and the RAG ingestion and retrieval components.

## 4. Logical Architecture Layers

### 4.1 API Layer

Technology: FastAPI

Responsibilities:
- Expose REST endpoints.
- Receive incident investigation requests.
- Validate incoming data.
- Initiate investigation workflows.
- Handle approval and rejection requests.
- Provide status and audit information.

### 4.2 Orchestration Layer

Technology: LangGraph

Responsibilities:
- Define the incident investigation workflow.
- Manage shared state.
- Coordinate agent execution.
- Support sequential and parallel processing.
- Manage conditional transitions.
- Maintain workflow checkpoints.
- Implement human-in-the-loop interruptions.

### 4.3 Agent Intelligence Layer

Components:
- Supervisor Agent
- Application Specialist
- Database Specialist
- Infrastructure Specialist
- Conflict Resolver
- Root Cause Analysis component
- Remediation Agent

Responsibilities:
- Coordinate investigation activities.
- Perform domain-specific analysis.
- Retrieve relevant historical information.
- Consolidate findings.
- Generate root-cause analysis.
- Recommend corrective actions.

### 4.4 Knowledge and AI Layer

Technologies:
- Ollama
- Qwen 2.5 7B
- Nomic Embed Text
- Qdrant

Responsibilities:
- Execute local LLM inference.
- Generate semantic embeddings.
- Store incident knowledge vectors.
- Retrieve relevant historical incidents.
- Supply contextual information to agents.

### 4.5 Enterprise Integration Layer

Component: Mock Enterprise API

Responsibilities:
- Retrieve incident details.
- Check service health.
- Create remediation recommendations.
- Handle corrective-action operations.
- Retrieve action status.
- Record audit events.

The current implementation uses mock enterprise APIs to demonstrate enterprise integration workflows.

### 4.6 Governance and Audit Layer

Responsibilities:
- Enforce authorization controls.
- Require human approval.
- Control remediation progression.
- Track approval decisions.
- Support status verification.
- Maintain audit records.

These are logical responsibilities implemented across the application rather than a separately deployed governance service.

## 5. Multi-Agent Architecture

The application follows a Supervisor-based multi-agent architecture.

The Supervisor coordinates the investigation and dispatches work to three specialist agents.

### Application Specialist

Investigates application-level symptoms, application errors and service behavior.

### Database Specialist

Investigates database-related symptoms, connectivity and database performance issues.

### Infrastructure Specialist

Investigates infrastructure-related symptoms, resource availability and infrastructure health.

Each specialist performs domain-specific investigation and can retrieve relevant knowledge through RAG.

## 6. Parallel Agent Execution

The specialist agents execute concurrently using the parallel workflow.

The architecture follows a fan-out/fan-in pattern.

Fan-out:
- Application Specialist executes.
- Database Specialist executes.
- Infrastructure Specialist executes.

Fan-in:
- Collect specialist findings.
- Consolidate investigation results.
- Pass the consolidated information to the Conflict Resolver.

Parallel execution reduces overall investigation latency compared with executing all independent investigations sequentially.

## 7. Conflict Resolution and Root Cause Analysis

Specialist agents may produce different or inconsistent findings.

The Conflict Resolver consolidates the findings and evaluates their consistency.

The RCA component uses the consolidated investigation evidence to develop a root-cause explanation.

The objective is to avoid making remediation decisions based on an isolated or potentially conflicting specialist finding.

## 8. Remediation Architecture

The Remediation Agent receives the investigation and RCA information.

It generates corrective-action recommendations and associated risk information.

The workflow incorporates a human approval checkpoint before proceeding with remediation.

LangGraph's `interrupt()` mechanism pauses workflow execution until an approval decision is supplied.

Approval and rejection decisions are handled through the application's approval workflow.

Execution and status verification follow the implemented remediation lifecycle controls.

## 9. RAG Architecture

The RAG subsystem provides historical incident knowledge to investigation agents.

The process consists of:

1. JSON-based knowledge ingestion.
2. Text extraction and preparation.
3. Text chunking.
4. Embedding generation using Nomic Embed Text through Ollama.
5. Vector storage in Qdrant.
6. Query embedding generation.
7. Similarity-based retrieval.
8. Context delivery to specialist agents.

The application also supports resolved-incident ingestion with validation of historical root-cause information.

Unverified root causes should not be treated as established historical knowledge.

## 10. State Management and Workflow Persistence

LangGraph maintains shared incident workflow state using a TypedDict-based structure.

The application uses MemorySaver for workflow checkpointing.

This supports the workflow's human approval interruption and subsequent resumption.

The checkpoint mechanism is part of the application's workflow execution model; it should not be interpreted as durable distributed production storage.

## 11. Enterprise Integration

The application integrates with a mock enterprise API.

The integration demonstrates operations such as:

- Incident retrieval.
- Service health checking.
- Remediation recommendation creation.
- Corrective-action execution operations.
- Action status retrieval.
- Audit event retrieval.

The mock integration allows the workflow to be demonstrated without requiring connectivity to actual enterprise ITSM or infrastructure systems.

## 12. Security and Governance

Security and governance are incorporated into the application through:

- Role-based authorization controls.
- Requester and role validation.
- Approval authorization.
- Human-in-the-loop remediation approval.
- Controlled workflow transitions.
- Audit event recording.

Detailed RBAC implementation and authorization responsibilities are documented separately in `security-and-rbac.md`.

## 13. Deployment Architecture

The application is containerized using Docker.

Docker Compose supports local application execution.

GitHub Actions provides automated build and testing pipeline activities.

The current deployment setup demonstrates containerized application execution and CI/CD automation.

Production deployment to a managed cloud environment would require additional infrastructure, monitoring, secrets management and operational controls.

## 14. Architectural Benefits

- Modular agent responsibilities.
- Parallel investigation capabilities.
- Contextual knowledge retrieval.
- Separation of orchestration and model execution.
- Structured root-cause and remediation workflows.
- Human approval and governance.
- Enterprise integration abstraction.
- Containerized execution.
- Extensible architecture.

## 15. Known Limitations

- Enterprise APIs are simulated through mock implementations.
- Local model performance depends on available hardware.
- MemorySaver is not a substitute for durable distributed workflow persistence.
- Production-scale concurrency and reliability require further validation.
- Enterprise monitoring and observability require additional implementation.
- Production integrations with actual ITSM and infrastructure platforms are not included in the current mock integration.

## 16. Conclusion

The AI Incident Investigation and Remediation Agent demonstrates an enterprise-oriented multi-agent architecture using LangGraph, RAG and locally hosted language models.

The architecture separates API management, agent orchestration, specialist investigation, knowledge retrieval, conflict resolution, remediation recommendation and governance responsibilities.

The use of parallel specialist agents, historical incident retrieval and human approval provides a structured foundation for intelligent incident investigation and controlled remediation.