import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_FILE = Path.home() / ".steam_ach_manager.log"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key.startswith("_"):
                continue
            if key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "asctime",
            }:
                continue
            payload[key] = value
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("steam_unlick")
    resolved_level = getattr(logging, str(level).upper(), logging.INFO)
    if logger.handlers:
        logger.setLevel(resolved_level)
        for h in logger.handlers:
            h.setLevel(resolved_level)
        return logger

    logger.setLevel(resolved_level)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setLevel(resolved_level)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    logger.info("logging_initialized", extra={"log_file": str(LOG_FILE), "level": logging.getLevelName(resolved_level)})
    return logger
