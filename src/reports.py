import pandas as pd


def expenses_by_weekday(df: pd.DataFrame) -> pd.DataFrame:
    """Группирует траты по дням недели и считает общую сумму для каждого дня."""
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

    return result


def expenses_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Группирует траты по категориям и считает общую сумму для каждой."""
    result = (
        df[df["Сумма операции"] < 0]
        .groupby("Категория")["Сумма операции"]
        .sum()
        .round()
        .reset_index()
        .rename(columns={"Сумма операции": "Итого расходов"})
        .sort_values("Итого расходов")  # от самых крупных к меньшим
    )

    return result


def expenses_work_vs_weekend(df: pd.DataFrame) -> pd.DataFrame:
    """Сравнивает траты в рабочие дни и в выходные."""
    df = df.copy()

    df["day_name"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True).dt.day_name()  # type: ignore
    # Если выходные: "Суббота", "Воскресенье"
    df["Тип дня"] = df["day_name"].apply(lambda x: "Выходной" if x in ["Saturday", "Sunday"] else "Рабочий день")

    result = (
        df[df["Сумма операции"] < 0]
        .groupby("Тип дня")["Сумма операции"]
        .sum()
        .round()
        .reset_index()
        .rename(columns={"Сумма операции": "Итого расходов"})
        .sort_values("Итого расходов")  # от самых крупных к меньшим
    )

    return result
