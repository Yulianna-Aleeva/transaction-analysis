import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

DATA_FILE = os.getenv(
    "DATA_FILE",
    str(BASE_DIR / "data" / "operations.xlsx"),
)

USER_SETTINGS_PATH = BASE_DIR / "user_settings.json"

with USER_SETTINGS_PATH.open(encoding="utf-8") as file:
    USER_SETTINGS = json.load(file)


LOG_LEVEL = logging.DEBUG
LOG_FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s: %(message)s"
FILE_MODE = "a"  # a - сохраняет, w - перезаписывает
ENCODING = "utf-8"


for name in ("urllib3", "yfinance", "peewee"):
    logging.getLogger(name).setLevel(logging.ERROR)


def get_logger(name_file: str) -> logging.Logger:
    """Создаёт отдельный лог-файл для каждого модуля."""
    # module_name = name_file.removeprefix("src.").replace(".", "_")  # чистое имя
    module_name = name_file
    if module_name == "__main__":
        # для прямого запуска
        import inspect

        frame = inspect.stack()[1]
        file_path = Path(frame.filename)
        try:
            rel_path = file_path.relative_to(BASE_DIR)
            module_name = ".".join(rel_path.with_suffix("").parts)
        except ValueError:
            # --- --- ---
            module_name = Path(sys.argv[0]).stem

    logger = logging.getLogger(module_name)
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(
            LOG_DIR / f"{module_name}.log",
            mode=FILE_MODE,
            encoding=ENCODING,
        )
        handler.setLevel(LOG_LEVEL)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

    return logger
