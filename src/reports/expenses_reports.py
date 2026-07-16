from typing import Optional
from typing import Sequence

import pandas as pd

from src.logs.log_config import get_logger
from src.utils.decorators import save_report

logger = get_logger(__name__)

REPORT_ERROR_LOG = 'Ошибка расчёта отчёта "%s": %s.'
REPORT_ERROR_USER = 'Ошибка расчёта отчёта "{report}": {error}.'
DAYS_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]


def _get_amount_rub_col(df: pd.DataFrame) -> str:
    """Возвращает имя колонки с суммой в рублях (опционально)."""
    return "amount_rub" if "amount_rub" in df.columns else "amount_operation"


@save_report()
def expenses_by_weekday(df: pd.DataFrame) -> pd.DataFrame:
    """Группирует траты по дням недели и считает общую сумму для каждого дня."""
    report_name = "Траты по дням недели"

    try:
        am_rub_col = _get_amount_rub_col(df)
        expenses = df[df[am_rub_col] < 0].copy()
        expenses["weekday"] = expenses["date_operation"].dt.dayofweek

        result = (
            expenses.groupby("weekday")[am_rub_col]
            .mean()
            .round(2)
            .reset_index()
            .assign(**{"День недели": lambda data: data["weekday"].map(lambda day: DAYS_RU[int(day)])})
            .drop(columns=["weekday"])
            .rename(columns={am_rub_col: "Итого расходов"})
        )

        result = result[["День недели", "Итого расходов"]]

        logger.debug("%s:\n%s", report_name, result)
        return result

    except Exception as error:
        logger.error(REPORT_ERROR_LOG, report_name, error, exc_info=True)
        raise ValueError(REPORT_ERROR_USER.format(report=report_name, error=error)) from error


@save_report()
def expenses_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Группирует траты по категориям и считает общую сумму для каждой."""
    report_name = "Траты по категориям"

    try:
        am_rub_col = _get_amount_rub_col(df)
        expenses = df[df[am_rub_col] < 0]

        result = (
            expenses.groupby("category")[am_rub_col]
            .sum()
            .round(2)
            .reset_index()
            .rename(columns={"category": "Категория", am_rub_col: "Итого расходов"})
            .sort_values("Итого расходов")
            .reset_index(drop=True)
        )

        logger.debug("%s: %s категорий", report_name, len(result))
        return result

    except Exception as error:
        logger.error(REPORT_ERROR_LOG, report_name, error, exc_info=True)
        raise ValueError(REPORT_ERROR_USER.format(report=report_name, error=error)) from error


@save_report()
def expenses_work_vs_weekend(df: pd.DataFrame, weekend_days: Optional[Sequence[str]] = None) -> pd.DataFrame:
    """Сравнивает траты в рабочие дни и в выходные."""
    report_name = "Траты в рабочие/выходные дни"
    weekend = set(weekend_days) if weekend_days is not None else {"Суббота", "Воскресенье"}

    try:
        am_rub_col = _get_amount_rub_col(df)
        expenses = df[df[am_rub_col] < 0].copy()
        expenses["day_name"] = expenses["date_operation"].dt.dayofweek.map(lambda day: DAYS_RU[int(day)])
        expenses["Тип дня"] = expenses["day_name"].apply(lambda day: "Выходной" if day in weekend else "Рабочий день")

        result = (
            expenses.groupby("Тип дня")[am_rub_col]
            .mean()
            .round(2)
            .reset_index()
            .rename(columns={am_rub_col: "Итого расходов"})
            .sort_values("Итого расходов")
            .reset_index(drop=True)
        )

        result = result[["Тип дня", "Итого расходов"]]

        logger.debug("%s:\n%s", report_name, result)
        return result

    except Exception as error:
        logger.error(REPORT_ERROR_LOG, report_name, error, exc_info=True)
        raise ValueError(REPORT_ERROR_USER.format(report=report_name, error=error)) from error
