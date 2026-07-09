from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from src.config import USER_SETTINGS, get_logger
from src.processor import format_date_column

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


def get_currency_rates() -> Dict[str, Optional[float]]:
    """Получает курсы валют и адрес API из настроек в user_settings.json."""
    url = USER_SETTINGS["currency_url"]
    codes = USER_SETTINGS["user_currencies"]
    result: Dict[str, Optional[float]] = {}

    resp = requests.get(url, timeout=8)
    resp.raise_for_status()
    data = resp.json()

    rates_block = data.get("Valute", {})
    for code in codes:
        val = rates_block.get(code)
        result[code] = round(float(val["Value"]), 2) if val and "Value" in val else None
    return result


def get_top_expenses(file_path: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Возвращает Топ-5 транзакций с самыми крупными расходами."""
    path = Path(file_path)
    if not path.exists():
        return []

    df = pd.read_excel(path, dtype=str)
    df = format_date_column(df)

    if "Сумма операции" not in df.columns:
        return []

    s = pd.to_numeric(df["Сумма операции"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    mask = s.notna() & (s < 0)

    top = (
        df[mask]
        .assign(sort_key=s)
        .sort_values("sort_key")  # от самых больших расходов к меньшим
        .head(limit)
        .drop(columns=["sort_key"], errors="ignore")
    )

    result = []
    for _, r in top.iterrows():
        raw_sum = r.get("Сумма операции", "")
        if not raw_sum or str(raw_sum).lower() == "nan":
            continue

        try:
            val = float(str(raw_sum).replace(",", "."))
            formatted = f"{abs(val):,.2f}".replace(",", " ").replace(".", ",")
        except (ValueError, TypeError):
            continue

        date_val = r.get("Дата операции", "")
        if str(date_val).lower() == "nan" or pd.isna(date_val):
            date_val = ""

        cat = r.get("Категория", "")
        desc = r.get("Описание", "")

        if str(cat).lower() == "nan":
            cat = ""
        if str(desc).lower() == "nan":
            desc = ""

        result.append(
            {
                "Дата": str(date_val),
                "Сумма": formatted,
                "Категория": cat,
                "Описание": desc,
            }
        )

    return result
