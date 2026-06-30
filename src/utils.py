from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from src.processor import format_date_column


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


def get_currency_rates() -> dict:
    """Получает курсы валют (сейчас - из ЦБ РФ) и возвращает словарь."""
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    codes = ["CNY", "USD", "EUR"]
    default_result = {code: None for code in codes}

    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        rates_block = data.get("Valute", {})

        result: Dict[str, Optional[float]] = {}
        for code in codes:
            val = rates_block.get(code)
            if val and "Value" in val:
                result[code] = round(float(val["Value"]), 2)
            else:
                result[code] = None
        return result

    except (requests.RequestException, ValueError, KeyError):
        return default_result


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
