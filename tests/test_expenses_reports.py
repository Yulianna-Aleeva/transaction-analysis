from pathlib import Path
from typing import Generator

import pandas as pd
import pytest

from src.reports.expenses_reports import (
    expenses_by_category,
    expenses_by_weekday,
    expenses_work_vs_weekend,
)


@pytest.fixture(autouse=True)
def change_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Переносит сохранение JSON-отчётов во временную папку."""
    monkeypatch.chdir(tmp_path)
    yield


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Тестовый обработанный DataFrame."""
    return pd.DataFrame(
        {
            "date_operation": pd.to_datetime(
                ["01.01.2024", "02.01.2024", "06.01.2024", "07.01.2024", "08.01.2024"],
                dayfirst=True,
            ),
            "amount_operation": [-150, -200, -300, -400, 1000],
            "category": ["Еда", "Еда", "Транспорт", "Аптека", "Пополнения"],
            "description": ["Магнит", "Пятёрочка", "Метро", "Аптека", "Зарплата"],
        }
    )


def test_expenses_by_weekday(sample_df: pd.DataFrame) -> None:
    """Отчёт группирует расходы по дням недели."""
    result = expenses_by_weekday(sample_df)

    assert result.to_dict(orient="records") == [
        {"День недели": "Понедельник", "Итого расходов": -150},
        {"День недели": "Вторник", "Итого расходов": -200},
        {"День недели": "Суббота", "Итого расходов": -300},
        {"День недели": "Воскресенье", "Итого расходов": -400},
    ]


def test_expenses_by_category(sample_df: pd.DataFrame) -> None:
    """Отчёт группирует расходы по категориям."""
    result = expenses_by_category(sample_df)

    assert result.to_dict(orient="records") == [
        {"Категория": "Аптека", "Итого расходов": -400},
        {"Категория": "Еда", "Итого расходов": -350},
        {"Категория": "Транспорт", "Итого расходов": -300},
    ]


def test_expenses_work_vs_weekend_default(sample_df: pd.DataFrame) -> None:
    """Отчёт сравнивает расходы в рабочие и выходные дни."""
    result = expenses_work_vs_weekend(sample_df)

    assert result.to_dict(orient="records") == [
        {"Тип дня": "Выходной", "Итого расходов": -350},
        {"Тип дня": "Рабочий день", "Итого расходов": -175},
    ]


def test_expenses_work_vs_weekend_custom_weekend(sample_df: pd.DataFrame) -> None:
    """Пользователь может задать свои выходные дни."""
    result = expenses_work_vs_weekend(sample_df, weekend_days=["Вторник"])

    assert result.to_dict(orient="records") == [
        {"Тип дня": "Рабочий день", "Итого расходов": -283.33},
        {"Тип дня": "Выходной", "Итого расходов": -200},
    ]


def test_reports_ignore_income(sample_df: pd.DataFrame) -> None:
    """Доходы не попадают в отчёты расходов."""
    result = expenses_by_category(sample_df)

    assert "Пополнения" not in result["Категория"].tolist()
    assert result["Итого расходов"].sum() == -1050


def test_expenses_by_weekday_error(sample_df: pd.DataFrame) -> None:
    """При ошибке отчёт выбрасывает ValueError."""
    broken_df = sample_df.drop(columns=["amount_operation"])

    with pytest.raises(ValueError, match="Ошибка расчёта отчёта"):
        expenses_by_weekday(broken_df)


def test_expenses_by_category_error(sample_df: pd.DataFrame) -> None:
    """При ошибке отчёт по категориям выбрасывает ValueError."""
    broken_df = sample_df.drop(columns=["category"])

    with pytest.raises(ValueError, match="Ошибка расчёта отчёта"):
        expenses_by_category(broken_df)


def test_expenses_work_vs_weekend_error(sample_df: pd.DataFrame) -> None:
    """При ошибке отчёт рабочие/выходные выбрасывает ValueError."""
    broken_df = sample_df.drop(columns=["date_operation"])

    with pytest.raises(ValueError, match="Ошибка расчёта отчёта"):
        expenses_work_vs_weekend(broken_df)
