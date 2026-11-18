# Technology Stack and Dependency Review

## 1. Introduction

The AI Incident Investigation and Remediation Agent is developed using Python and an agent-based architecture to automate enterprise incident investigation, root-cause analysis, knowledge retrieval, remediation recommendation and approval workflows.

The solution combines Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), vector search, multi-agent orchestration and REST API integration.

The technology stack has been selected to support modularity, extensibility, local AI model execution, structured workflow orchestration and enterprise integration.

## 2. Technology Stack Overview

| Category | Technology | Purpose |
|---|---|---|
| Programming Language | Python 3.12 | Application development |
| Backend Framework | FastAPI | REST API development |
| ASGI Server | Uvicorn | Application hosting |
| Agent Orchestration | LangGraph | Stateful agent workflow orchestration |
| AI Abstractions | LangChain Core | Supporting AI abstractions |
| LLM Runtime | Ollama | Local LLM execution |
| LLM Model | Qwen 2.5 7B | Investigation and reasoning |
| Embedding Model | Nomic Embed Text | Semantic embedding generation |
| Vector Database | Qdrant | Vector storage and similarity retrieval |
| Document Processing | PDF processing | Knowledge document ingestion |
| Data Validation | Pydantic | Request and response validation |
| Configuration | python-dotenv | Environment configuration |
| Containerization | Docker | Application containerization |
| Container Orchestration | Docker Compose | Local container management |
| Testing | Pytest | Automated testing |
| CI/CD | GitHub Actions | Automated build and test pipeline |
| Source Control | Git and GitHub | Version management |

## 3. Programming Language and Backend Framework

### 3.1 Python

Python is the primary programming language used for implementing the application.

Reasons for selection:
- Strong ecosystem for AI and machine learning.
- Native integration with LangGraph and Qdrant.
- Supports asynchronous API development.
- Suitable for implementing modular agent workflows.
- Extensive ecosystem for enterprise integrations.

### 3.2 FastAPI

FastAPI provides the REST API layer for exposing application capabilities.

Responsibilities:
- Accept incident investigation requests.
- Validate incoming request data.
- Trigger agent workflows.
- Manage approval-related API operations.
- Return structured responses to API consumers.

### 3.3 Uvicorn

Uvicorn is used as the ASGI server for hosting the FastAPI application.

It provides the application execution environment and supports asynchronous request processing.

## 4. Agent Orchestration Framework

### 4.1 LangGraph

LangGraph is the primary agent orchestration framework.

It manages stateful workflows and coordinates the execution of multiple agents.

Responsibilities:
- Define workflow nodes and transitions.
- Maintain shared workflow state.
- Support conditional execution.
- Coordinate sequential and parallel agent execution.
- Manage conflict-resolution stages.
- Support human-in-the-loop approval using workflow interruptions.
- Control workflow progression based on execution results.

LangGraph was selected because the application requires more than a simple linear LLM chain. Incident investigation involves multiple stages, conditional decisions, agent coordination and approval checkpoints.

### 4.2 LangChain Core

LangChain Core provides foundational AI abstractions used by the LangChain ecosystem.

It complements LangGraph but is not the primary workflow orchestration framework in this application.

## 5. Large Language Model and Embedding Technologies

### 5.1 Ollama

Ollama is used as the local model runtime.

It allows the application to communicate with locally hosted language and embedding models.

Benefits:
- Local model execution.
- Reduced dependency on external model APIs during development.
- Greater control over model selection.
- No mandatory commercial LLM API subscription for local execution.

The application uses a custom Ollama client for model communication.

### 5.2 Qwen 2.5 7B

Qwen 2.5 7B is the configured language model.

It supports:
- Incident analysis.
- Root-cause investigation.
- Natural-language reasoning.
- Remediation recommendation generation.

### 5.3 Nomic Embed Text

Nomic Embed Text is the configured embedding model.

It converts textual knowledge into numerical vector representations.

These embeddings are used for semantic retrieval from the incident knowledge base.

## 6. Retrieval-Augmented Generation and Vector Database

### 6.1 Qdrant

Qdrant is used as the vector database.

It stores vector representations of incident knowledge and enables similarity-based retrieval.

Responsibilities:
- Store incident knowledge embeddings.
- Maintain the incident knowledge collection.
- Retrieve semantically relevant historical information.
- Provide relevant context to investigation agents.

Configured collection:

`incident_knowledge`

Configured embedding dimension:

`768`

### 6.2 RAG Implementation

The RAG pipeline consists of:

1. Document ingestion.
2. Text extraction.
3. Text chunking.
4. Embedding generation.
5. Vector storage in Qdrant.
6. Similarity-based retrieval.
7. Context injection into agent workflows.

RAG allows agents to use relevant historical incident knowledge rather than relying exclusively on the language model's pretrained knowledge.

## 7. Document Processing

PDF documents are part of the knowledge ingestion process.

The dependency file includes PyPDF for PDF processing.

The exact active PDF extraction implementation should be verified against the ingestion source before attributing a specific extraction library to the runtime workflow.

## 8. Application Configuration and Validation

### 8.1 Pydantic

Pydantic provides data validation and structured data models.

It is used to validate API request and response structures.

### 8.2 Python-dotenv

Python-dotenv loads environment variables from the application's environment configuration files.

It helps separate application configuration from source code.

## 9. Dependency Inventory

The following versions were captured from the project's existing Python virtual environment.

| Package | Installed Version | Purpose |
|---|---:|---|
| fastapi | 0.162.5 | REST API framework |
| uvicorn | 0.54.0 | ASGI server |
| langgraph | 1.2.20 | Agent orchestration |
| langchain-core | 1.8.0 | AI abstractions |
| langchain-openai | 1.7.4 | OpenAI integration package |
| qdrant-client | 1.20.0 | Vector database client |
| fastembed | 0.9.1 | Optional embedding integration |
| pydantic | 2.14.3 | Data validation |
| python-dotenv | 1.2.4 | Environment configuration |
| pypdf | 7.0.1 | PDF processing library |
| pytest | 9.2.0 | Automated testing |
| httpx | 0.28.1 | HTTP client |
| tenacity | 9.2.1 | Retry handling |

### 9.1 Dependency Usage Assessment

The following dependencies have direct imports confirmed in the inspected application or test files:

- FastAPI
- Pydantic
- LangGraph
- Qdrant Client
- Python-dotenv
- Pytest

Uvicorn is used as the application server rather than imported by the application code.

The following packages are installed but their direct application usage was not established by the source-import review:

- langchain-openai
- pypdf
- httpx
- tenacity
- FastEmbed

LangChain Core is installed as part of the LangChain ecosystem and is also a dependency of LangGraph.

The above distinction is important because an installed package is not necessarily an actively used application dependency.

## 10. Infrastructure and DevOps Technologies

### 10.1 Docker

Docker is used to package the application into a container.

Benefits:
- Consistent application execution.
- Environment isolation.
- Simplified deployment.
- Portability across compatible environments.

### 10.2 Docker Compose

Docker Compose supports local container management and application execution.

### 10.3 GitHub Actions

GitHub Actions automates the CI/CD pipeline.

The project's pipeline includes automated testing and Docker image build activities.

### 10.4 Git and GitHub

Git and GitHub are used for source control, collaboration and repository management.

## 11. Technology Selection Rationale

The technology stack was selected based on the following architectural considerations:

| Requirement | Selected Technology | Justification |
|---|---|---|
| API development | FastAPI | Lightweight Python REST framework |
| Agent orchestration | LangGraph | Stateful and conditional workflows |
| Local LLM execution | Ollama | Local model hosting |
| Language reasoning | Qwen 2.5 7B | Configured language model |
| Embedding generation | Nomic Embed Text | Semantic vector generation |
| Vector storage | Qdrant | Similarity-based retrieval |
| Data validation | Pydantic | Structured validation |
| Containerization | Docker | Portable application packaging |
| Automated testing | Pytest | Repeatable testing |
| CI/CD | GitHub Actions | Automated build and test |

## 12. Dependency Version Management

The current requirements.txt contains unpinned package declarations.

The installed versions were captured from the existing virtual environment using pip freeze.

The dependency health check was executed using pip check.

Result:

`No broken requirements found.`

For reproducible enterprise deployments, dependency versions should be explicitly controlled and validated through a tested dependency-locking strategy.

The current working environment has been retained without package upgrades or removals.

## 13. Architecture Extensibility

The architecture separates the following responsibilities:

- API layer.
- Agent orchestration.
- Language model execution.
- Embedding generation.
- Vector retrieval.
- Enterprise API integration.

This separation provides opportunities for future enhancements.

Potential future technology alternatives include:

- Azure OpenAI or Azure AI Foundry for managed model hosting.
- Azure AI Search for managed enterprise retrieval.
- Azure Container Apps or AKS for cloud deployment.
- Managed Qdrant or another enterprise vector database.
- Enterprise monitoring and distributed tracing.

These are potential future enhancements and should not be interpreted as currently implemented capabilities.

## 14. Known Technology Limitations

1. The current model execution depends on locally hosted Ollama services.
2. Local model performance depends on available hardware resources.
3. The configured LLM is a 7B parameter model and may have reasoning limitations for complex production incidents.
4. Qdrant availability and persistence depend on the configured deployment mode.
5. The current mock enterprise APIs demonstrate integration workflows but do not represent real enterprise system integrations.
6. The requirements file does not currently pin package versions.
7. Some installed dependencies have not yet been established as actively used by the application.
8. Production deployment would require additional operational monitoring, secrets management, access governance and scalability validation.

## 15. Conclusion

The project uses a modular Python-based AI architecture combining LangGraph, Ollama, Qdrant and FastAPI.

LangGraph coordinates the investigation and remediation workflows, Ollama provides local LLM and embedding execution, and Qdrant supports retrieval of historical incident knowledge.

Docker and GitHub Actions provide the containerization and CI/CD foundation.

The technology stack provides a foundation for demonstrating enterprise-oriented agent orchestration, RAG-based investigation, controlled remediation and human approval workflows.