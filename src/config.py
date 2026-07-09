import json
import logging
import os
from pathlib import Path
from typing import Optional, TypedDict

from dotenv import load_dotenv

load_dotenv()


class LoggingConfig(TypedDict):
    log_level: int
    log_format: str
    file_mode: str
    encoding: str


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.getenv("DATA_FILE", os.path.join(BASE_DIR, "data", "operations.xlsx"))
USER_SETTINGS_PATH = os.path.join(BASE_DIR, "user_settings.json")
with open(USER_SETTINGS_PATH, encoding="utf-8") as f:
    USER_SETTINGS = json.load(f)
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING_CONFIG: LoggingConfig = {
    "log_level": logging.DEBUG,
    "log_format": "%(asctime)s %(name)-12s %(levelname)-8s: %(message)s",
    "file_mode": "w",  # "a" (append) сохраняет старые логи при перезапуске
    "encoding": "utf-8",
}


def get_logger(log_name: Optional[str] = None) -> logging.Logger:
    """Функция для получения готового логгера в любом файле."""
    if log_name is None or log_name == "__main__":
        module_name = Path(__file__).stem
    else:
        module_name = log_name.replace("src.", "").replace(".", "_")

    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if not logger.handlers:
        log_file = os.path.join(LOG_DIR, f"{module_name}.log")
        handler = logging.FileHandler(log_file, mode=LOGGING_CONFIG["file_mode"], encoding=LOGGING_CONFIG["encoding"])
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(LOGGING_CONFIG["log_format"]))
        logger.addHandler(handler)

    return logger
