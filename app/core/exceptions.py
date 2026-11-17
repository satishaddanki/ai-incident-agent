
class IncidentAgentError(Exception):
    """Base exception for the entire incident management application."""


class EnterpriseAPIError(IncidentAgentError):
    """Base exception for enterprise API failures."""


class AuthorizationError(EnterpriseAPIError):
    """Raised when a user lacks required permissions."""


class ApprovalRequiredError(EnterpriseAPIError):
    """Raised when human approval is missing or invalid."""


class InvalidActionError(EnterpriseAPIError):
    """Raised when an action is not allowlisted."""


class MockAPITimeoutError(TimeoutError, IncidentAgentError):
    """Simulates a timeout after a remote action has completed."""


class AgentExecutionError(IncidentAgentError):
    """Raised when an AI specialist agent fails."""


class ExternalServiceError(IncidentAgentError):
    """Raised when an external dependency is unavailable."""


class WorkflowExecutionError(IncidentAgentError):
    """Raised when the LangGraph workflow cannot continue."""


class ValidationError(IncidentAgentError):
    """Raised when input or output validation fails."""


class ActionExecutionError(IncidentAgentError):
    """Raised when corrective-action execution fails."""
