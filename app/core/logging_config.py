
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIRECTORY = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIRECTORY / "incident_agent.log"

_CONFIGURED = False


def configure_logging(
    log_level: int = logging.INFO,
) -> None:
    """
    Configure centralized application logging.

    Logs are written to both console and rotating log files.
    """

    global _CONFIGURED

    if _CONFIGURED:
        return

    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    console_handler = logging.StreamHandler()

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    application_logger = logging.getLogger("incident_agent")

    application_logger.setLevel(log_level)
    application_logger.propagate = False

    application_logger.addHandler(file_handler)
    application_logger.addHandler(console_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a named application logger.

    Example:
        logger = get_logger(__name__)
    """

    configure_logging()

    return logging.getLogger(
        f"incident_agent.{name}"
    )
