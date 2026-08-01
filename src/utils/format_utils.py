from datetime import datetime
from typing import Any
from typing import Dict

import pandas as pd

from src.log_config import get_logger

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


def convert_to_rub(df: pd.DataFrame, rates: list[Dict[str, Any]]) -> pd.DataFrame:
    """Конвертирует валюту в рубли по актуальным курсам ЦБ РФ."""
    df = df.copy()
    rates_dict = {r["currency"]: r["rate"] for r in rates}
    foreign_currency = df["currency_operation"].map(rates_dict).fillna(1.0)
    df["amount_rub"] = (df["amount_operation"] * foreign_currency).round(2)

    logger.debug("Конвертирование в рубли завершено. Курсы: %s.", rates_dict)
    return df


def format_rub(amount: Any) -> str:
    """Форматирует сумму в формат: X XXX XXX,XX."""
    if pd.isna(amount) or amount is None:
        return "0,00"
    return f"{float(amount):,.2f}".replace(",", " ").replace(".", ",")


def format_rub_rounded(amount: Any) -> str:
    if pd.isna(amount) or amount is None:
        return "0"
    value = float(amount)
    rounded = round(value)
    if rounded == 0:
        return "0"

    return f"{float(amount):,.0f}".replace(",", " ").replace(".", ",")
