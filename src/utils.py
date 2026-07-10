from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from logs.config import DATA_FILE, get_logger
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


MAPPING = {
    "Дата операции": "date_operation",
    "Дата платежа": "date_payment",
    "Номер карты": "card_number",
    "Статус": "status",
    "Сумма операции": "amount_operation",
    "Валюта операции": "currency_operation",
    "Сумма платежа": "amount_payment",
    "Валюта платежа": "currency_payment",
    "Кэшбэк": "cashback",
    "Категория": "category",
    "MCC": "mcc",
    "Описание": "description",
    "Бонусы (включая кэшбэк)": "bonuses_total",
    "Округление на инвесткопилку": "invest_rounding",
    "Сумма операции с округлением": "amount_operation_rounded",
}


def load_transaction(file_path: str = DATA_FILE) -> pd.DataFrame:
    """Загружает данные из Excel-файла, переименовывает колонки и приводит дату к datetime (dd.mm.yyyy)."""
    try:
        df = pd.read_excel(file_path)
        # Переименовываем только колонки из файла
        rename_dict = {old: new for old, new in MAPPING.items() if old in df.columns}
        df = df.rename(columns=rename_dict)

        # Приводим дату к datetime (dd.mm.yyyy)
        if "date_operation" in df.columns:
            df["date_operation"] = pd.to_datetime(df["date_operation"], dayfirst=True, errors="coerce")
        else:
            logger.warning("Колонка 'date_operation' не найдена.")
        # Логирование типов дат в колонке "Дата операции"
        logger.debug(f"Тип date_operation:\n{df['date_operation'].dtype}")
        # Логирование переименованных колонок
        if rename_dict:
            renamed_info = [f"{old} → {new}" for old, new in rename_dict.items()]
            logger.info(f"Загружено строк: {len(df)}")
            logger.debug("Переименованы колонки:\n" + "\n".join(renamed_info))
        else:
            logger.info(f"Загружено строк: {len(df)} (колонки не переименовывались)")
        return df
    except Exception as e:
        logger.error(f"Ошибка загрузки файла {file_path}: {e}")
        return pd.DataFrame()


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
