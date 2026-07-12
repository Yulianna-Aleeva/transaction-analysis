import pandas as pd
import pytest

from src.views import get_cards_info, get_events_page_data


@pytest.fixture
def cards_df() -> pd.DataFrame:
    """DataFrame с расходами по двум картам и одним доходом."""
    return pd.DataFrame(
        {
            "card_number": ["*7197", "*7197", "*5814", "*5814"],
            "amount_operation": [-100.0, -300.0, -50.0, 1000.0],
            "category": ["Еда", "Такси", "Кафе", "Зарплата"],
        }
    )


def test_get_cards_info(cards_df: pd.DataFrame) -> None:
    """Считает расходы и кешбэк (1%) по каждой карте."""
    result = get_cards_info(cards_df)

    assert len(result) == 2

    # Карта 5814: расход 50, кешбэк 0.5
    card_5814 = next(c for c in result if c["last_digits"] == "5814")
    assert card_5814["total_spent"] == 50.0
    assert card_5814["cashback"] == 0.5

    # Карта 7197: расход 400 (100+300), кешбэк 4.0
    card_7197 = next(c for c in result if c["last_digits"] == "7197")
    assert card_7197["total_spent"] == 400.0
    assert card_7197["cashback"] == 4.0


def test_get_cards_info_empty() -> None:
    """Пустой DataFrame возвращает пустой список."""
    empty_df = pd.DataFrame({"card_number": [], "amount_operation": []})
    assert get_cards_info(empty_df) == []


def test_get_cards_info_no_expenses() -> None:
    """Если нет расходов (только доходы), возвращается пустой список."""
    df = pd.DataFrame(
        {
            "card_number": ["*7197"],
            "amount_operation": [5000.0],
        }
    )
    assert get_cards_info(df) == []


def test_get_events_page_data(cards_df: pd.DataFrame) -> None:
    """Проверяет агрегацию расходов с топ-7, остальным и переводами/наличными."""
    df = cards_df.copy()
    df["date_operation"] = pd.to_datetime(["2021-12-01"] * len(df))
    date_str = "2021-12-31 23:59:59"

    result = get_events_page_data(date_str, df)

    for item in result["expenses"]["main"]:
        assert isinstance(item["amount"], int)
    assert isinstance(result["expenses"]["total_amount"], int)

    assert result["expenses"]["total_amount"] == 450
    assert result["expenses"]["transfers_and_cash"] == []
    assert result["income"]["total_amount"] == 1000
