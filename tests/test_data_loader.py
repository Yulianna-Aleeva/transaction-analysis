from typing import Any
from unittest.mock import Mock
from unittest.mock import patch

import pandas as pd
import pytest
from pandas.api.types import is_datetime64_any_dtype
from pandas.api.types import is_numeric_dtype

from src.utils.data_loader import load_transaction
from src.utils.format_utils import format_rub

MODULE_PATH = "src.utils.data_loader"


@pytest.fixture
def raw_df() -> pd.DataFrame:
    """Корректный сырой датафрейм."""
    return pd.DataFrame(
        {
            "Дата операции": ["31.12.2021", "01.01.2022"],
            "Номер карты": ["*4556", "*7197"],
            "Статус": ["OK", "OK"],
            "Сумма операции": ["-160.89", "1000"],
            "Валюта операции": ["RUB", "USD"],
            "Кэшбэк": [1.61, 0.00],
            "Категория": ["Супермаркеты", "Пополнения"],
            "Описание": ["Магнит", "Перевод"],
        }
    )


@pytest.fixture
def cards_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "card_number": ["*7197", "*7197", "*5814", "*5814", "*5814"],
            "amount_rub": [-100.0, -300.0, -50.0, 1000.0, -200.0],
            "category": ["Еда", "Такси", "Кафе", "Зарплата", "Переводы"],
        }
    )  # pragma: no cover


@patch("src.utils.data_loader.get_all_currency_rates")
@patch("src.utils.data_loader.convert_to_rub")
@patch(f"{MODULE_PATH}.pd.read_excel")
def test_load_transaction_success(
    mock_read_excel: Mock,
    mock_convert: Mock,
    mock_get_rates: Mock,
    raw_df: pd.DataFrame,
) -> None:
    """Успешная загрузка с конвертацией валют."""
    mock_read_excel.return_value = raw_df.copy()
    mock_get_rates.return_value = {"USD": 75.0, "RUB": 1.0}

    def fake_convert(dff: pd.DataFrame, rates_list: list[dict[str, Any]]) -> pd.DataFrame:
        dff = dff.copy()
        dff["amount_rub"] = dff["amount_operation"] * dff["currency_operation"].map(
            {r["currency"]: r["rate"] for r in rates_list}
        ).fillna(1.0)
        return dff

    mock_convert.side_effect = fake_convert

    result = load_transaction("test.xlsx")

    assert "date_operation" in result.columns
    assert "amount_operation" in result.columns
    assert "amount_rub" in result.columns
    assert "currency_operation" in result.columns
    assert "category" in result.columns
    assert "description" in result.columns

    assert is_datetime64_any_dtype(result["date_operation"])
    assert is_numeric_dtype(result["amount_rub"])

    assert result.loc[0, "category"] == "Супермаркеты"
    assert result.loc[0, "amount_rub"] == pytest.approx(-160.89)
    assert result.loc[1, "amount_rub"] == pytest.approx(75000.0)

    assert "amount_rub_formatted" in result.columns
    assert "amount_rub_rounded" in result.columns
    assert result.iloc[0]["amount_rub_formatted"] == format_rub(result.iloc[0]["amount_rub"])


def test_load_transaction_missing_required_column(raw_df: pd.DataFrame) -> None:
    """Нет обязательной колонки."""
    broken_df = raw_df.drop(columns=["Описание"])

    with patch(f"{MODULE_PATH}.pd.read_excel", return_value=broken_df):
        with pytest.raises(ValueError, match="Отсутствуют обязательные колонки"):
            load_transaction("test.xlsx")


def test_load_transaction_read_excel_error() -> None:
    """Ошибка чтения Excel-файла."""
    with patch(f"{MODULE_PATH}.pd.read_excel", side_effect=FileNotFoundError("Файл не найден")):
        with pytest.raises(ValueError, match="Ошибка загрузки файла"):
            load_transaction("missing.xlsx")


def test_load_transaction_partial_bad_dates(raw_df: pd.DataFrame) -> None:
    """Плохие даты становятся NaT, но загрузка не падает."""
    mixed_df = raw_df.copy()
    mixed_df["Дата операции"] = ["31.12.2021", "не дата"]

    with (
        patch("src.utils.data_loader.get_all_currency_rates") as mock_rates,
        patch("src.utils.data_loader.convert_to_rub") as mock_conv,
    ):
        mock_rates.return_value = {"RUB": 1.0}
        mock_conv.side_effect = lambda dff, _: dff.assign(
            amount_rub=pd.to_numeric(dff["amount_operation"], errors="coerce"),
            amount_rub_formatted=dff["amount_operation"],
            amount_rub_rounded=0,
        )

        with patch(f"{MODULE_PATH}.pd.read_excel", return_value=mixed_df):
            result = load_transaction("test.xlsx")

    assert pd.notna(result.loc[0, "date_operation"])
    assert pd.isna(result.loc[1, "date_operation"])


def test_load_transaction_filter_failed(raw_df: pd.DataFrame) -> None:
    """FAILED статусы отфильтровываются."""
    df = raw_df.copy()
    df.loc[1, "Статус"] = "FAILED"

    with (
        patch("src.utils.data_loader.get_all_currency_rates") as mock_rates,
        patch("src.utils.data_loader.convert_to_rub") as mock_conv,
    ):
        mock_rates.return_value = {"RUB": 1.0, "USD": 75.0}
        mock_conv.side_effect = lambda dff, _: dff.assign(
            amount_rub=pd.to_numeric(dff["amount_operation"], errors="coerce"),
            amount_rub_formatted=dff["amount_operation"],
            amount_rub_rounded=0,
        )

        with patch(f"{MODULE_PATH}.pd.read_excel", return_value=df):
            result = load_transaction("test.xlsx")

    assert len(result) == 1
    assert result.iloc[0]["status"] == "OK"
