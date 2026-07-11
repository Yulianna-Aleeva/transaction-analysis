import pandas as pd

from src.logs.log_config import get_logger
from src.utils.decorators import save_report

logger = get_logger(__name__)


@save_report()
def expenses_by_weekday(df: pd.DataFrame) -> pd.DataFrame:
    """Группирует траты по дням недели и считает общую сумму для каждого дня."""
    try:
        days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

        result = (
            df[df["Сумма операции"] < 0]
            .assign(date=lambda x: pd.to_datetime(x["Дата операции"], errors="coerce", dayfirst=True))
            .assign(**{"День недели": lambda x: x["date"].dt.dayofweek})
            .groupby("День недели")["Сумма операции"]
            .sum()
            .round()
            .reset_index()
            .assign(**{"День недели": lambda x: x["День недели"].map(lambda i: days[i])})
            .rename(columns={"Сумма операции": "Итого расходов"})
        )

        logger.debug("Траты по дням недели: %d строк", len(result))
        return result

    except Exception as error:
        logger.error("Ошибка расчёта трат по дням недели: %s", error)
        return df.head(0)


@save_report()
def expenses_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Группирует траты по категориям и считает общую сумму для каждой."""
    try:
        result = (
            df[df["Сумма операции"] < 0]
            .groupby("Категория")["Сумма операции"]
            .sum()
            .round()
            .reset_index()
            .rename(columns={"Сумма операции": "Итого расходов"})
            .sort_values("Итого расходов")
        )

        logger.debug("Траты по категориям: %d строк", len(result))
        return result

    except Exception as error:
        logger.error("Ошибка расчёта трат по категориям: %s", error)
        return df.head(0)


@save_report()
def expenses_work_vs_weekend(df: pd.DataFrame) -> pd.DataFrame:
    """Сравнивает траты в рабочие дни и в выходные."""
    try:
        temp = df.copy()
        temp["day_name"] = pd.to_datetime(temp["Дата операции"], errors="coerce", dayfirst=True).dt.day_name()
        temp["Тип дня"] = temp["day_name"].apply(
            lambda x: "Выходной" if x in ["Saturday", "Sunday"] else "Рабочий день"
        )

        result = (
            temp[temp["Сумма операции"] < 0]
            .groupby("Тип дня")["Сумма операции"]
            .sum()
            .round()
            .reset_index()
            .rename(columns={"Сумма операции": "Итого расходов"})
            .sort_values("Итого расходов")
        )

        logger.debug("Траты рабочие/выходные: %d строк", len(result))
        return result

    except Exception as error:
        logger.error("Ошибка расчёта рабочие/выходные: %s", error)
        return df.head(0)
