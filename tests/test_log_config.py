import logging
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from src.logs import log_config


def clear_logger_handlers(logger_name: str) -> None:
    """Очищает handlers у логгера перед тестом."""
    logger = logging.getLogger(logger_name)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_get_logger_creates_log_file(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """get_logger создаёт лог-файл в LOG_DIR."""
    logger_name = "src.test_module"
    monkeypatch.setattr(log_config, "LOG_DIR", tmp_path)
    clear_logger_handlers(logger_name)

    logger = log_config.get_logger(logger_name)
    logger.info("Проверка логирования")

    for handler in logger.handlers:
        handler.flush()

    log_file = tmp_path / f"{logger_name}.log"

    assert logger.name == logger_name
    assert logger.level == log_config.LOG_LEVEL
    assert logger.propagate is False
    assert log_file.exists()
    assert "Проверка логирования" in log_file.read_text(encoding=log_config.ENCODING)


def test_get_logger_does_not_duplicate_handlers(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Повторный вызов get_logger не добавляет лишние handlers."""
    logger_name = "src.test_duplicate"
    monkeypatch.setattr(log_config, "LOG_DIR", tmp_path)
    clear_logger_handlers(logger_name)

    logger_1 = log_config.get_logger(logger_name)
    logger_2 = log_config.get_logger(logger_name)

    assert logger_1 is logger_2
    assert len(logger_2.handlers) == 1


def test_external_loggers_have_error_level() -> None:
    """Сторонние логгеры имеют уровень ERROR."""
    assert logging.getLogger("urllib3").level == logging.ERROR
    assert logging.getLogger("yfinance").level == logging.ERROR
    assert logging.getLogger("peewee").level == logging.ERROR
