
import logging

from app.core.logging_config import (
    configure_logging,
    get_logger,
    LOG_FILE,
)

from app.core.exceptions import (
    IncidentAgentError,
    EnterpriseAPIError,
    AuthorizationError,
    MockAPITimeoutError,
)


def test_logger_creation():

    logger = get_logger("test_module")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "incident_agent.test_module"


def test_log_file_creation():

    configure_logging()

    assert LOG_FILE.exists()


def test_exception_hierarchy():

    assert issubclass(
        EnterpriseAPIError,
        IncidentAgentError,
    )

    assert issubclass(
        AuthorizationError,
        EnterpriseAPIError,
    )


def test_timeout_exception_hierarchy():

    assert issubclass(
        MockAPITimeoutError,
        TimeoutError,
    )

    assert issubclass(
        MockAPITimeoutError,
        IncidentAgentError,
    )
