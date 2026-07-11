from datetime import datetime

import pandas as pd
import pytest

from src.utils.filters_utils import (
    filter_last_3_months,
    get_top_positions,
    sort_df_by_column,
)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Тестовый DataFrame."""
    return pd.DataFrame(
        {
            "date_operation": pd.to_datetime(
                ["01.01.2024", "15.02.2024", "01.04.2024", "15.05.2024"],
                dayfirst=True,
            ),
            "amount_operation": [-100, -500, -200, -1000],
            "category": ["Еда", "Транспорт", "Еда", "Аптека"],
        }
    )


def test_sort_df_by_column_ascending(sample_df: pd.DataFrame) -> None:
    """Сортировка по возрастанию."""
    result = sort_df_by_column(sample_df, "amount_operation", ascending=True)
    assert result["amount_operation"].tolist() == [-1000, -500, -200, -100]


def test_sort_df_by_column_descending(sample_df: pd.DataFrame) -> None:
    """Сортировка по убыванию."""
    result = sort_df_by_column(sample_df, "amount_operation", ascending=False)
    assert result["amount_operation"].tolist() == [-100, -200, -500, -1000]


def test_sort_df_by_column_missing_column(sample_df: pd.DataFrame) -> None:
    """Ошибка при отсутствии колонки для сортировки."""
    with pytest.raises(ValueError, match='Колонка "missing" для сортировки не найдена'):
        sort_df_by_column(sample_df, "missing")


def test_get_top_positions_default(sample_df: pd.DataFrame) -> None:
    """ТОП-N по убыванию."""
    result = get_top_positions(sample_df, "amount_operation", n=2, ascending=False)
    assert len(result) == 2
    assert result["amount_operation"].tolist() == [-100, -200]
    assert result.index.tolist() == [0, 1]


def test_get_top_positions_expenses(sample_df: pd.DataFrame) -> None:
    """ТОП расходов: самые крупные отрицательные суммы."""
    result = get_top_positions(sample_df, "amount_operation", n=2, ascending=True)
    assert result["amount_operation"].tolist() == [-1000, -500]


def test_get_top_positions_missing_column(sample_df: pd.DataFrame) -> None:
    """Ошибка при отсутствии колонки для ТОП."""
    with pytest.raises(ValueError, match='Колонка "missing" для вывода ТОП-5 не найдена'):
        get_top_positions(sample_df, "missing")


def test_filter_last_3_months_by_max_date(sample_df: pd.DataFrame) -> None:
    """Фильтр последних 3 месяцев от максимальной даты."""
    result = filter_last_3_months(sample_df)
    assert result["date_operation"].min() >= pd.Timestamp("2024-02-15")
    assert result["date_operation"].max() <= pd.Timestamp("2024-05-15")
    assert len(result) == 3


def test_filter_last_3_months_by_user_date(sample_df: pd.DataFrame) -> None:
    """Фильтр последних 3 месяцев от пользовательской даты."""
    result = filter_last_3_months(sample_df, "01.04.2024")
    assert result["date_operation"].tolist() == [
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-02-15"),
        pd.Timestamp("2024-04-01"),
    ]


def test_filter_last_3_months_by_datetime(sample_df: pd.DataFrame) -> None:
    """Фильтр принимает datetime."""
    result = filter_last_3_months(sample_df, datetime(2024, 4, 1))
    assert len(result) == 3


def test_filter_last_3_months_bad_date(sample_df: pd.DataFrame) -> None:
    """Некорректная конечная дата возвращает пустой DataFrame."""
    result = filter_last_3_months(sample_df, "не дата")
    assert result.empty
    assert list(result.columns) == list(sample_df.columns)
