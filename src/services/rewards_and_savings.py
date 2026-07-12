from typing import Any, Dict, List

import pandas as pd

from src.logs.log_config import get_logger

logger = get_logger(__name__)


def top_cashback_categories(df: pd.DataFrame, year: int, month: int) -> List[Dict[str, Any]]:
    """Возвращает топ категорий по сумме кешбэка за указанный месяц."""
    try:
        if "cashback" not in df.columns:
            logger.warning("Колонка 'cashback' отсутствует.")
            return []
        period = df[(df["date_operation"].dt.year == year) & (df["date_operation"].dt.month == month)].copy()
        if period.empty:
            logger.debug("Нет транзакций за %s-%s", year, month)
            return []
        cash = period.groupby("category")["cashback"].sum().reset_index()
        cash = cash[cash["cashback"] > 0].sort_values("cashback", ascending=False)
        result = cash.head(3).to_dict(orient="records")
        for item in result:
            item["cashback"] = round(item["cashback"], 2)
        logger.debug("Топ-кешбэк за %s-%s: %s", year, month, result)
        return result  # type: ignore[no-any-return]
    except Exception as e:
        logger.error("Ошибка расчёта кешбэка: %s", e, exc_info=True)
        return []
