from typing import Optional

import pandas as pd

from src.logs.log_config import get_logger

logger = get_logger(__name__)


def sort_df_by_column(df: pd.DataFrame, column: str, ascending: bool = True) -> pd.DataFrame:
    """Сортирует DataFrame по колонке."""
    if column not in df.columns:
        logger.error("Колонка для сортировки не найдена: %s", column)
        raise ValueError(f"Колонка не найдена: {column}")

    logger.debug("Сортировка по колонке %s, ascending=%s", column, ascending)
    return df.sort_values(by=column, ascending=ascending)


def get_top_positions(df: pd.DataFrame, column: str, n: int = 5, ascending: bool = False) -> pd.DataFrame:
    """Возвращает ТОП-N строк по колонке."""
    if column not in df.columns:
        logger.error("Колонка для ТОП не найдена: %s", column)
        raise ValueError(f"Колонка не найдена: {column}")

    logger.debug("ТОП-%s по колонке %s, ascending=%s", n, column, ascending)
    return df.sort_values(by=column, ascending=ascending).head(n)


def filter_last_3_months(df: pd.DataFrame, end_date: Optional[str] = None) -> pd.DataFrame:
    """Фильтр последних 3 месяцев по date_operation."""
    end = pd.to_datetime(end_date, dayfirst=True, errors="coerce") if end_date else df["date_operation"].max()
    if pd.isna(end):
        return df.head(0)

    start = end - pd.DateOffset(months=3)
    logger.debug("Фильтр периода: %s - %s", start.date(), end.date())
    return df[df["date_operation"].between(start, end)]
