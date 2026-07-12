from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from src.utils.format_utils import (
    convert_to_rub,
    current_date,
    format_rub,
    greeting_time,
)

MODULE_PATH = "src.utils.format_utils"


def test_current_date() -> None:
    """Проверяет формат возвращаемой текущей даты."""
    with patch(f"{MODULE_PATH}.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2024, 1, 31)
        assert current_date() == "31.01.2024"


@pytest.mark.parametrize(
    "hour, expected",
    [
        (6, "Доброе утро"),
        (11, "Доброе утро"),
        (12, "Добрый день"),
        (17, "Добрый день"),
        (18, "Добрый вечер"),
        (22, "Добрый вечер"),
        (23, "Доброй ночи"),
        (0, "Доброй ночи"),
        (5, "Доброй ночи"),
    ],
)
def test_greeting_time(hour: int, expected: str) -> None:
    """Проверяет приветствие по времени суток."""
    with patch(f"{MODULE_PATH}.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2024, 1, 31, hour)
        assert greeting_time() == expected


def test_convert_to_rub() -> None:
    """Проверяет конвертацию валют: известные перемножаются, неизвестные и рубли * 1.0."""
    df = pd.DataFrame(
        {
            "currency_operation": ["USD", "EUR", "RUB", "CNY"],
            "amount_operation": [100.0, 50.0, 500.0, 200.0],
        }
    )
    rates = [
        {"currency": "USD", "rate": 90.0},
        {"currency": "EUR", "rate": 100.0},
    ]

    result = convert_to_rub(df, rates)

    assert "amount_rub" in result.columns
    # USD (100*90), EUR (50*100), RUB (500*1), CNY (200*1) <=
    assert result["amount_rub"].tolist() == [9000.0, 5000.0, 500.0, 200.0]


def test_format_rub_valid() -> None:
    """Проверяет форматирование корректных сумм."""
    assert format_rub(1234567.89) == "1 234 567,89"
    assert format_rub(100) == "100,00"
    assert format_rub(-50.5) == "-50,50"
    assert format_rub("1000") == "1 000,00"


def test_format_rub_empty() -> None:
    """Проверяет форматирование пустых значений (NaN, None)."""
    assert format_rub(None) == "0,00"
    assert format_rub(pd.NA) == "0,00"
    import numpy as np

    assert format_rub(np.nan) == "0,00"
