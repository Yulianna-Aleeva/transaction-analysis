from datetime import datetime

import pandas as pd

from src.logs.log_config import get_logger

logger = get_logger(__name__)


def sort_df_by_column(df: pd.DataFrame, column: str, ascending: bool = True) -> pd.DataFrame:
    """Сортирует DataFrame по колонке."""
    if column not in df.columns:
        logger.error('Колонка "%s" для сортировки не найдена.', column)
        raise ValueError(f'Колонка "{column}" для сортировки не найдена.')
    logger.debug('Сортировка по колонке "%s", ascending=%s.', column, ascending)
    return df.sort_values(by=column, ascending=ascending)


def get_top_positions(df: pd.DataFrame, column: str, n: int = 5, ascending: bool = False) -> pd.DataFrame:
    """Возвращает ТОП-N строк по колонке. По умолчанию: 5. False: по убыванию, True: по возрастанию."""
    if column not in df.columns:
        logger.error('Колонка "%s" для вывода ТОП-%s не найдена.', column, n)
        raise ValueError(f'Колонка "{column}" для вывода ТОП-{n} не найдена.')
    logger.debug('ТОП-%s по колонке "%s", ascending=%s', n, column, ascending)
    return df.sort_values(by=column, ascending=ascending, kind="mergesort").reset_index(drop=True)


def filter_last_3_months(df: pd.DataFrame, end_date: str | datetime | None = None) -> pd.DataFrame:
    """Фильтр последних 3 месяцев по date_operation."""
    end = pd.to_datetime(end_date, dayfirst=True, errors="coerce") if end_date else df["date_operation"].max()
    if pd.isna(end):
        logger.warning("Не удалось определить конечную дату для фильтра.")
        return df.head(0)
    start = end - pd.DateOffset(months=3)
    result = df[df["date_operation"].between(start, end)]
    logger.debug("Фильтр периода: %s - %s. Строк: %s.", start.date(), end.date(), len(result))
    return result
