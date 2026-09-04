"""
Structured JSON Logging for FINRES.
Provides machine-parseable logs that integrate with ELK, Loki, or any log aggregator.
"""
import json
import logging
import sys
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Format log records as one-line JSON for production log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "ts": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else "Exception",
                "message": str(record.exc_info[1]) if record.exc_info[1] else "",
                "traceback": self.formatException(record.exc_info),
            }
        for key in ("request_id", "customer_id", "user_id", "module", "duration_ms", "status_code"):
            val = getattr(record, key, None)
            if val is not None:
                log_obj[key] = val
        return json.dumps(log_obj, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with JSON output to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


def get_logger(name: str) -> logging.Logger:
    """Get a named logger that inherits the JSON formatter."""
    return logging.getLogger(name)


def log_performance(metric_name: str):
    """Decorator that logs execution time of any function."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger("finres.perf")
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000
                logger.info(
                    f"{metric_name} completed",
                    extra={"module": metric_name, "duration_ms": round(duration, 2), "status_code": 200}
                )
                return result
            except Exception as e:
                duration = (time.perf_counter() - start) * 1000
                logger.error(
                    f"{metric_name} failed: {e}",
                    extra={"module": metric_name, "duration_ms": round(duration, 2), "status_code": 500},
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


def log_request(request_id: str, method: str, path: str, status_code: int, duration_ms: float, user_id: Optional[str] = None) -> None:
    """Log a single HTTP request with full context."""
    get_logger("finres.api").info(
        f"{method} {path} -> {status_code}",
        extra={
            "request_id": request_id,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "user_id": user_id,
        }
    )