from datetime import datetime

from src.logs.log_config import get_logger

logger = get_logger(__name__)


def current_date() -> str:
    """Возвращает текущую дату."""
    return datetime.now().strftime("%d.%m.%Y")


def greeting_time() -> str:
    """Возвращает приветствие в зависимости от текущего времени суток."""
    current_hour = datetime.now().hour
    if 6 <= current_hour < 12:
        return "Доброе утро"
    elif 12 <= current_hour < 18:
        return "Добрый день"
    elif 18 <= current_hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"
