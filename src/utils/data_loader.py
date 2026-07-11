import pandas as pd

from src.logs.log_config import DATA_FILE, get_logger

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

REQUIRED_COLUMNS = {"date_operation", "amount_operation", "category", "description"}


def load_transaction(file_path: str = DATA_FILE) -> pd.DataFrame:
    """Загружает данные из Excel-файла, переименовывает колонки и приводит дату к datetime (dd.mm.yyyy)."""
    try:
        df = pd.read_excel(file_path)
        rename_dict = {old: new for old, new in MAPPING.items() if old in df.columns}
        df = df.rename(columns=rename_dict)
        missing_columns = REQUIRED_COLUMNS - set(df.columns)
        if missing_columns:
            raise ValueError(f"Отсутствуют обязательные колонки: {', '.join(missing_columns)}.")

        # Приводим дату к datetime (dd.mm.yyyy)
        df["date_operation"] = pd.to_datetime(df["date_operation"], dayfirst=True, errors="coerce")
        # Логирование типов дат в колонке "Дата операции"
        logger.debug("Тип date_operation: %s", df["date_operation"].dtype)
        # Логирование переименованных колонок
        if rename_dict:
            renamed_info = [f"{old} → {new}" for old, new in rename_dict.items()]
            logger.info("Загружено строк: ", len(df))
            logger.debug("Переименованы колонки:\n%s", "\n".join(renamed_info))
        else:
            logger.info("Загружено строк: %s (колонки не переименовывались).", len(df))
        return df
    except Exception as e:
        logger.error("Ошибка загрузки файла %s: %s", file_path, e)
        return pd.DataFrame()
