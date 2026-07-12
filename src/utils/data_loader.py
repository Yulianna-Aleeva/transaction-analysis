import pandas as pd

from src.api.api_currency import get_all_currency_rates
from src.logs.log_config import DATA_FILE, get_logger
from src.utils.format_utils import convert_to_rub

logger = get_logger(__name__)


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
REVERSE_MAPPING = {v: k for k, v in MAPPING.items()}
REQUIRED_COLUMNS_RUS = {
    "Дата операции",
    "Номер карты",
    "Статус",
    "Сумма операции",
    "Валюта операции",
    "Кэшбэк",
    "Категория",
    "Описание",
}


def load_transaction(file_path: str = DATA_FILE) -> pd.DataFrame:
    """Загружает данные из Excel-файла и проверяет на обязательные колонки."""
    try:
        df = pd.read_excel(file_path)
        missing_columns = REQUIRED_COLUMNS_RUS - set(df.columns)
        if missing_columns:
            msg = "Отсутствуют обязательные колонки:\n" + "\n".join(f"- {c}" for c in missing_columns)
            logger.debug(msg)
            raise ValueError(msg)
        return _parse_transactions(df)
    except Exception as e:
        logger.error("Ошибка загрузки файла %s: %s", file_path, e, exc_info=True)
        raise ValueError(f"Ошибка загрузки файла {file_path}: {e}") from e


def _parse_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Переименовывает колонки, обрабатывает даты, суммы,
    отбрасывает статус FAILED и конвертирует валюты в рубли.
    """
    # Переименовываем колонки с русского на английский по словарю "MAPPING"
    rename_dict = {old: new for old, new in MAPPING.items() if old in df.columns}
    df = df.rename(columns=rename_dict)

    # Отбрасываем FAILED
    if "status" in df.columns:
        df = df[df["status"] == "OK"].copy()

    # Проверяем суммы операций
    df["amount_operation"] = pd.to_numeric(df["amount_operation"], errors="coerce")

    # Приводим даты к datetime
    df["date_operation"] = pd.to_datetime(df["date_operation"], format="mixed", dayfirst=True, errors="coerce")
    df["date_operation"] = df["date_operation"].dt.normalize()

    # Конвертируем все валюты в рубли
    all_rates = get_all_currency_rates()
    rates_list = [{"currency": c, "rate": r} for c, r in all_rates.items()]
    df = convert_to_rub(df, rates_list)
    logger.info("Обработано строк: %s.", len(df))
    return df
