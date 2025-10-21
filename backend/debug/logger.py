"""Structured logging infrastructure for the LR(1) Parser Visualizer."""

import json
import logging
import os
import sys
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional

# Debug configuration
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
JSON_LOGGING = os.getenv("JSON_LOGGING", "false").lower() in ("true", "1", "yes")


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""

    def format(self, record):
        if JSON_LOGGING:
            return self._format_json(record)
        else:
            return self._format_text(record)

    def _format_json(self, record):
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data, default=str)

    def _format_text(self, record):
        """Format log record as human-readable text."""
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        level_emoji = {"TRACE": "🔍", "DEBUG": "🐛", "INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "CRITICAL": "💥"}.get(
            record.levelname, "📝"
        )

        base_msg = f"{level_emoji} [{timestamp}] {record.levelname:8} {record.name:20} {record.getMessage()}"

        # Add extra data if present
        if hasattr(record, "extra_data") and record.extra_data:
            extra_str = " | ".join(f"{k}={v}" for k, v in record.extra_data.items())
            base_msg += f" | {extra_str}"

        return base_msg


def setup_logging(level: str = LOG_LEVEL, json_format: bool = JSON_LOGGING) -> logging.Logger:
    """Setup logging configuration."""
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level, logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    # Add trace level if in debug mode
    if DEBUG:
        logging.addLevelName(5, "TRACE")

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module."""
    return logging.getLogger(name)


def log_structured(level: int, message: str, logger: logging.Logger, **kwargs):
    """Log a structured message with extra data."""
    extra_data = {k: v for k, v in kwargs.items() if v is not None}
    logger.log(level, message, extra={"extra_data": extra_data})


def trace(message: str, logger: logging.Logger, **kwargs):
    """Log a trace message."""
    if DEBUG:
        log_structured(5, message, logger, **kwargs)


def debug(message: str, logger: logging.Logger, **kwargs):
    """Log a debug message."""
    log_structured(logging.DEBUG, message, logger, **kwargs)


def info(message: str, logger: logging.Logger, **kwargs):
    """Log an info message."""
    log_structured(logging.INFO, message, logger, **kwargs)


def warning(message: str, logger: logging.Logger, **kwargs):
    """Log a warning message."""
    log_structured(logging.WARNING, message, logger, **kwargs)


def error(message: str, logger: logging.Logger, **kwargs):
    """Log an error message."""
    log_structured(logging.ERROR, message, logger, **kwargs)


def critical(message: str, logger: logging.Logger, **kwargs):
    """Log a critical message."""
    log_structured(logging.CRITICAL, message, logger, **kwargs)


@contextmanager
def log_section(logger: logging.Logger, section_name: str, **context_data):
    """Context manager for logging sections."""
    logger.info(f"Starting {section_name}", **context_data)
    start_time = datetime.now()

    try:
        yield
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Completed {section_name}", duration_ms=f"{duration * 1000:.2f}")
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Failed {section_name}", error=str(e), duration_ms=f"{duration * 1000:.2f}")
        raise


def log_function_call(func_name: str, args: tuple = (), kwargs: Dict[str, Any] = None, logger: logging.Logger = None):
    """Log function call with arguments."""
    if logger is None:
        logger = get_logger("function_calls")

    if DEBUG:
        debug(f"Calling {func_name}", logger, args=str(args)[:100], kwargs=str(kwargs or {})[:100])


def log_function_result(func_name: str, result: Any = None, duration: float = None, logger: logging.Logger = None):
    """Log function result."""
    if logger is None:
        logger = get_logger("function_calls")

    if DEBUG:
        result_str = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
        debug(f"Completed {func_name}", logger, result=result_str, duration_ms=f"{duration * 1000:.2f}" if duration else None)


def debug_timer(func):
    """Decorator to time function execution and log it."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not DEBUG:
            return func(*args, **kwargs)

        logger = get_logger(f"{func.__module__}.{func.__name__}")
        func_name = f"{func.__module__}.{func.__name__}"

        log_function_call(func_name, args, kwargs, logger)
        start_time = datetime.now()

        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            log_function_result(func_name, result, duration, logger)
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error(f"Failed {func_name}", logger, error=str(e), duration_ms=f"{duration * 1000:.2f}")
            raise

    return wrapper


def log_api_request(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, logger: logging.Logger = None):
    """Log API request."""
    if logger is None:
        logger = get_logger("api")

    info(f"{method} {endpoint}", logger, **data or {})


def log_api_response(endpoint: str, status_code: int, data: Optional[Dict[str, Any]] = None, logger: logging.Logger = None):
    """Log API response."""
    if logger is None:
        logger = get_logger("api")

    if 200 <= status_code < 300:
        info(f"Response {status_code} for {endpoint}", logger, **data or {})
    else:
        error(f"Response {status_code} for {endpoint}", logger, **data or {})


# Initialize logging
setup_logging()
