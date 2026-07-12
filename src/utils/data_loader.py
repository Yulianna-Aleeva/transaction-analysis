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
REVERSE_MAPPING = {v: k for k, v in MAPPING.items()}
REQUIRED_COLUMNS_RUS = {"Дата операции", "Сумма операции", "Валюта операции", "Категория", "Описание"}


def load_transaction(file_path: str = DATA_FILE) -> pd.DataFrame:
    """Загружает данные из Excel-файла, переименовывает колонки и приводит дату к datetime (dd.mm.yyyy)."""
    try:
        df = pd.read_excel(file_path)

        missing_columns = REQUIRED_COLUMNS_RUS - set(df.columns)
        if missing_columns:
            logger.debug("Отсутствуют обязательные колонки:\n%s", "\n ".join(missing_columns))
            raise ValueError("Отсутствуют обязательные колонки:\n" + "\n".join(f"- {col}" for col in missing_columns))

        # Переименовываем колонки, присутствующие в файле
        rename_dict = {old: new for old, new in MAPPING.items() if old in df.columns}
        df = df.rename(columns=rename_dict)

        # Приводим дату к datetime (dd.mm.yyyy)
        df["date_operation"] = pd.to_datetime(df["date_operation"], format="mixed", dayfirst=True, errors="coerce")
        df["date_operation"] = df["date_operation"].dt.normalize()

        if df["date_operation"].isna().all():
            logger.debug('Колонка "%s" не распознана (все значения NaT).', REVERSE_MAPPING["date_operation"])
            raise ValueError(f'Колонка "{REVERSE_MAPPING["date_operation"]}" не распознана.')

        df["amount_operation"] = pd.to_numeric(df["amount_operation"], errors="coerce")
        if df["amount_operation"].isna().all():
            logger.debug('Колонка "%s" не распознана (все значения NaN).', REVERSE_MAPPING["amount_operation"])
            raise ValueError(f'Колонка "{REVERSE_MAPPING["amount_operation"]}" не распознана.')

        # Логирование
        logger.info("Загружено строк: %s.", len(df))
        # Логирование типов
        logger.debug("Тип date_operation: %s", df["date_operation"].dtype)
        logger.debug("Тип amount_operation: %s", df["amount_operation"].dtype)

        # Логирование переименованных колонок
        if rename_dict:
            renamed_info = [f"{old} → {new}" for old, new in rename_dict.items()]
            logger.debug("Переименованы колонки:\n%s", "\n".join(renamed_info))
        else:
            logger.info("Загружено строк: %s (колонки не переименовывались).", len(df))  # pragma: no cover
        return df

    except Exception as e:
        logger.error("Ошибка загрузки файла %s: %s", file_path, e, exc_info=True)
        raise ValueError(f"Ошибка загрузки файла {file_path}: {e}") from e
