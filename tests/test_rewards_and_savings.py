import pandas as pd

from src.services.rewards_and_savings import top_cashback_categories


class TestCashback:
    def test_top_cashback_categories(self) -> None:
        df = pd.DataFrame(
            {
                "date_operation": pd.to_datetime(["2024-01-01"] * 5),
                "category": ["Еда", "Транспорт", "Одежда", "Еда", "Транспорт"],
                "cashback": [10.0, 5.0, 20.0, 15.0, 0.0],
            }
        )
        result = top_cashback_categories(df, 2024, 1)
        expected = [
            {"category": "Еда", "cashback": 25.0},
            {"category": "Одежда", "cashback": 20.0},
            {"category": "Транспорт", "cashback": 5.0},
        ]
        assert result == expected

    def test_empty_when_no_data(self) -> None:
        df = pd.DataFrame({"date_operation": pd.to_datetime(["2024-01-01"]), "category": ["Еда"], "cashback": [0.0]})
        result = top_cashback_categories(df, 2024, 2)
        assert result == []

    def test_no_cashback_column(self) -> None:
        df = pd.DataFrame({"date_operation": pd.to_datetime(["2024-01-01"]), "category": ["Еда"]})
        result = top_cashback_categories(df, 2024, 1)
        assert result == []
