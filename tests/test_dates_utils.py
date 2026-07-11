from datetime import datetime
from unittest.mock import patch

import pytest

from src.utils.dates_utils import current_date, greeting_time

MODULE_PATH = "src.utils.dates_utils"


def test_current_date() -> None:
    """Проверяет формат текущей даты."""
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
