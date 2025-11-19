from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Any, Dict

FALLBACK_LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}


def _load_yaml_config(config_path: Path) -> Dict[str, Any] | None:
    try:
        import yaml  # type: ignore
    except ImportError:  # pragma: no cover - optional dependency
        logging.getLogger(__name__).warning(
            "PyYAML not installed; falling back to default logging config.",
        )
        return None

    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def configure_logging() -> None:
    """Apply logging configuration, falling back to sane defaults when needed."""
    repo_root = Path(__file__).resolve().parents[5]
    config_path = repo_root / "configs" / "logging" / "backend-logging.yaml"

    if config_path.exists():
        config_dict = _load_yaml_config(config_path)
        if config_dict:
            logging.config.dictConfig(config_dict)
            return

    logging.config.dictConfig(FALLBACK_LOGGING_CONFIG)
