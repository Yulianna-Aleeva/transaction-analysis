import pandas as pd
import pytest

from src.views import get_cards_info
from src.views import get_events_page_data
from src.views import get_main_page_data


@pytest.fixture
def cards_df() -> pd.DataFrame:
    """DataFrame с расходами по двум картам и одним доходом."""
    return pd.DataFrame(
        {
            "card_number": ["*7197", "*7197", "*5814", "*5814", "*5814"],
            "amount_rub": [-100.0, -300.0, -50.0, 1000.0, -200.0],
            "amount_operation": [-100.0, -300.0, -50.0, 1000.0, -200.0],
            "category": ["Еда", "Такси", "Кафе", "Зарплата", "Переводы"],
            "description": ["Магнит", "Яндекс.Такси", "Кофе", "Зарплата", "Перевод ФЛ"],
        }
    )


def test_get_cards_info(cards_df: pd.DataFrame) -> None:
    """Считает расходы и кешбэк (1%) по каждой карте."""
    result = get_cards_info(cards_df)

    assert len(result) == 2

    card_5814 = next(c for c in result if c["last_digits"] == "5814")
    assert card_5814["total_spent"] == 250.0
    assert card_5814["cashback"] == 2.5

    card_7197 = next(c for c in result if c["last_digits"] == "7197")
    assert card_7197["total_spent"] == 400.0
    assert card_7197["cashback"] == 4.0


def test_get_cards_info_empty() -> None:
    """Пустой DataFrame возвращает пустой список."""
    empty_df = pd.DataFrame({"card_number": [], "amount_rub": []})
    assert get_cards_info(empty_df) == []


def test_get_cards_info_no_expenses() -> None:
    """Если нет расходов (только доходы), возвращается пустой список."""
    df = pd.DataFrame({"card_number": ["*7197"], "amount_rub": [5000.0]})
    assert get_cards_info(df) == []


def test_get_main_page_normal_date(cards_df: pd.DataFrame) -> None:
    """Главная страница с явной датой."""
    df = cards_df.copy()
    df["date_operation"] = pd.to_datetime(["2021-12-01"] * len(df))
    result = get_main_page_data("2021-12-31 23:59:59", df)

    assert "greeting" in result
    assert len(result["cards"]) == 2
    assert len(result["top_transactions"]) == 5
    assert result["currency_rates"] is not None
    assert result["stock_prices"] is not None


def test_get_main_page_with_last_date(cards_df: pd.DataFrame) -> None:
    """Главная страница с use_last_date=True."""
    df = cards_df.copy()
    df["date_operation"] = pd.to_datetime(["2021-12-01"] * len(df))
    result = get_main_page_data("", df, use_last_date=True)

    assert "greeting" in result
    assert len(result["cards"]) == 2


def test_get_main_page_empty_period(cards_df: pd.DataFrame) -> None:
    """Дата вне диапазона данных – карты и топ пустые."""
    df = cards_df.copy()
    df["date_operation"] = pd.to_datetime(["2021-12-01"] * len(df))
    result = get_main_page_data("2020-01-01 00:00:00", df)

    assert result["cards"] == []
    assert result["top_transactions"] == []


def test_get_main_page_exception() -> None:
    """При ошибке возвращается ключ 'error'."""
    df = pd.DataFrame({"x": [1]})
    result = get_main_page_data("2021-12-31 23:59:59", df)
    assert "error" in result


def test_get_events_page_data(cards_df: pd.DataFrame) -> None:
    """События: расходы, переводы, поступления, округление до целых."""
    df = cards_df.copy()
    df["date_operation"] = pd.to_datetime(["2021-12-01"] * len(df))
    date_str = "2021-12-31 23:59:59"

    result = get_events_page_data(date_str, df)

    assert "error" not in result
    assert "expenses" in result
    assert "income" in result

    assert isinstance(result["expenses"]["total_amount"], int)
    for item in result["expenses"]["main"]:
        assert isinstance(item["amount"], int)
    for item in result["expenses"]["transfers_and_cash"]:
        assert isinstance(item["amount"], int)
    assert isinstance(result["income"]["total_amount"], int)
    for item in result["income"]["main"]:
        assert isinstance(item["amount"], int)


def test_get_events_page_empty_period(cards_df: pd.DataFrame) -> None:
    """Пустой период – нулевые суммы."""
    df = cards_df.copy()
    df["date_operation"] = pd.to_datetime(["2021-12-01"] * len(df))
    result = get_events_page_data("2020-01-01 00:00:00", df)

    assert result["expenses"]["total_amount"] == 0
    assert result["income"]["total_amount"] == 0


def test_get_events_page_exception() -> None:
    """Исключение в событиях – ключ 'error'."""
    df = pd.DataFrame({"x": [1]})
    result = get_events_page_data("2021-12-31 23:59:59", df)
    assert "error" in result


def test_get_cards_info_no_card_number_column() -> None:
    """При отсутствии колонки card_number возвращается пустой список."""
    df = pd.DataFrame({"amount_rub": [-100.0], "category": ["Еда"]})
    result = get_cards_info(df)
    assert result == []


def test_get_main_page_invalid_date_uses_now(cards_df: pd.DataFrame) -> None:
    """Пустая строка даты → NaT → используется pd.Timestamp.now()."""
    df = cards_df.copy()
    df["date_operation"] = pd.to_datetime(["2021-12-01"] * len(df))
    result = get_main_page_data("", df)
    assert "greeting" in result
    assert result["cards"] == []
    assert result["top_transactions"] == []


def test_get_events_page_invalid_date_uses_last(cards_df: pd.DataFrame) -> None:
    """Невалидная дата → используется последняя дата файла."""
    df = cards_df.copy()
    df["date_operation"] = pd.to_datetime(["2021-12-01"] * len(df))
    result = get_events_page_data("не дата", df)
    assert "error" not in result
    assert result["expenses"]["total_amount"] > 0


def test_get_events_page_with_many_categories() -> None:
    """Более 7 категорий → остальные попадают в «Остальное»."""
    df = pd.DataFrame(
        {
            "date_operation": pd.to_datetime(["2021-12-01"] * 9),
            "amount_rub": [-100, -200, -300, -400, -500, -600, -700, -800, -900],
            "category": ["A", "B", "C", "D", "E", "F", "G", "H", "I"],
            "description": [""] * 9,
        }
    )
    result = get_events_page_data("2021-12-31 23:59:59", df)
    main = result["expenses"]["main"]

    assert len(main) == 8
    ost = [m for m in main if m["category"] == "Остальное"]
    assert len(ost) == 1
    assert ost[0]["amount"] == 300
