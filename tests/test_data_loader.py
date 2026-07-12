from unittest.mock import patch

import pandas as pd
import pytest
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

from src.utils.data_loader import load_transaction

MODULE_PATH = "src.utils.data_loader"


@pytest.fixture
def raw_df() -> pd.DataFrame:
    """Корректный сырой датафрейм."""
    return pd.DataFrame(
        {
            "Дата операции": ["31.12.2021", "01.01.2022"],
            "Сумма операции": ["-160.89", "1000"],
            "Валюта операции": ["RUB", "USD"],
            "Категория": ["Супермаркеты", "Пополнения"],
            "Описание": ["Магнит", "Перевод"],
        }
    )


def test_load_transaction_success(raw_df: pd.DataFrame) -> None:
    """Успешная загрузка и переименование колонок."""
    with patch(f"{MODULE_PATH}.pd.read_excel", return_value=raw_df):
        result = load_transaction("test.xlsx")

    assert "date_operation" in result.columns
    assert "amount_operation" in result.columns
    assert "currency_operation" in result.columns
    assert "category" in result.columns
    assert "description" in result.columns

    assert is_datetime64_any_dtype(result["date_operation"])
    assert is_numeric_dtype(result["amount_operation"])

    assert result.loc[0, "category"] == "Супермаркеты"
    assert result.loc[0, "description"] == "Магнит"
    assert result.loc[0, "amount_operation"] == -160.89


def test_load_transaction_missing_required_column(raw_df: pd.DataFrame) -> None:
    """Нет обязательной колонки."""
    broken_df = raw_df.drop(columns=["Описание"])

    with patch(f"{MODULE_PATH}.pd.read_excel", return_value=broken_df):
        with pytest.raises(ValueError, match="Отсутствуют обязательные колонки"):
            load_transaction("test.xlsx")


def test_load_transaction_bad_date(raw_df: pd.DataFrame) -> None:
    """Дата операции не распознана."""
    broken_df = raw_df.copy()
    broken_df["Дата операции"] = ["ошибка", "не дата"]

    with patch(f"{MODULE_PATH}.pd.read_excel", return_value=broken_df):
        with pytest.raises(ValueError, match="не распознана"):
            load_transaction("test.xlsx")


def test_load_transaction_bad_amount(raw_df: pd.DataFrame) -> None:
    """Сумма операции не распознана."""
    broken_df = raw_df.copy()
    broken_df["Сумма операции"] = ["abc", "ошибка"]

    with patch(f"{MODULE_PATH}.pd.read_excel", return_value=broken_df):
        with pytest.raises(ValueError, match="не распознана"):
            load_transaction("test.xlsx")


def test_load_transaction_read_excel_error() -> None:
    """Ошибка чтения Excel-файла."""
    with patch(f"{MODULE_PATH}.pd.read_excel", side_effect=FileNotFoundError("Файл не найден")):
        with pytest.raises(ValueError, match="Ошибка загрузки файла"):
            load_transaction("missing.xlsx")


def test_load_transaction_partial_bad_values(raw_df: pd.DataFrame) -> None:
    """Частично плохие даты и суммы не ломают загрузку."""
    mixed_df = raw_df.copy()
    mixed_df["Дата операции"] = ["31.12.2021", "не дата"]
    mixed_df["Сумма операции"] = ["-160.89", "abc"]

    with patch(f"{MODULE_PATH}.pd.read_excel", return_value=mixed_df):
        result = load_transaction("test.xlsx")

    assert pd.notna(result.loc[0, "date_operation"])
    assert pd.isna(result.loc[1, "date_operation"])
    assert result.loc[0, "amount_operation"] == -160.89
    assert pd.isna(result.loc[1, "amount_operation"])
