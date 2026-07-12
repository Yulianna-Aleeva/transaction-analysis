from unittest.mock import patch

import pandas as pd
import pytest

from src.services.search_services import search_transfers, simple_search

MODULE_PATH = "src.api.search"


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Тестовый DataFrame с разными типами данных."""
    return pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            "description": [
                "Покупка в МАГНИТ на 1000 руб",
                "Оплата Ozon заказ 123",
                "Колхоз 160 га посевов",
                "Услуги C++ разработка",
                "Штраф ГИБДД $100.50 (тест)",
            ],
            "category": ["Продукты", "Онлайн-покупки", "Сельское хозяйство", "IT-услуги", "Штрафы"],
            "amount": [1000, 500, 160, 2000, 100.50],
        }
    )


class TestSimpleSearch:

    def test_empty_query(self, sample_df: pd.DataFrame) -> None:
        """Пустой запрос — возвращается исходный DataFrame."""
        result = simple_search(sample_df, "")
        pd.testing.assert_frame_equal(result, sample_df)

    def test_case_insensitive_single_word(self, sample_df: pd.DataFrame) -> None:
        """Поиск одного слова без учёта регистра."""
        result_lower = simple_search(sample_df, "магнит")
        result_upper = simple_search(sample_df, "МАГНИТ")
        assert len(result_lower) == 1
        assert len(result_upper) == 1
        assert result_lower.iloc[0]["description"] == "Покупка в МАГНИТ на 1000 руб"

    def test_and_logic(self, sample_df: pd.DataFrame) -> None:
        """Логика AND: все слова должны присутствовать в строке."""
        result = simple_search(sample_df, "Колхоз 160")
        assert len(result) == 1
        assert result.iloc[0]["description"] == "Колхоз 160 га посевов"

    def test_or_fallback(self, sample_df: pd.DataFrame) -> None:
        """Логика OR: если AND не дал результатов, возвращаются строки с любым словом."""
        result = simple_search(sample_df, "Магнит Ozon")
        assert len(result) == 2
        descriptions = result["description"].tolist()
        assert "Покупка в МАГНИТ на 1000 руб" in descriptions
        assert "Оплата Ozon заказ 123" in descriptions

    def test_special_characters(self, sample_df: pd.DataFrame) -> None:
        """Поиск текста со спецсимволами (regex=False)."""
        result_cpp = simple_search(sample_df, "C++")
        assert len(result_cpp) == 1
        assert "C++" in result_cpp.iloc[0]["description"]

        result_money = simple_search(sample_df, "$100.50")
        assert len(result_money) == 1
        assert "$100.50" in result_money.iloc[0]["description"]

        result_paren = simple_search(sample_df, "(тест)")
        assert len(result_paren) == 1
        assert "(тест)" in result_paren.iloc[0]["description"]

    def test_no_match_returns_empty(self, sample_df: pd.DataFrame) -> None:
        """Если ничего не найдено даже в режиме OR — пустой DataFrame."""
        result = simple_search(sample_df, "НесуществующееСлово")
        assert result.empty
        assert list(result.columns) == list(sample_df.columns)

    def test_query_with_extra_spaces(self, sample_df: pd.DataFrame) -> None:
        """Запрос с лишними пробелами обкорректно обрабатывается."""
        result = simple_search(sample_df, "  Колхоз   160  ")
        assert len(result) == 1

    def test_simple_search_exception(self, sample_df: pd.DataFrame) -> None:
        """Покрывает ветку except при возникновении ошибки."""
        df = pd.DataFrame({"description": ["тестовая строка"]})

        with patch.object(pd.DataFrame, "apply", side_effect=ValueError("Ошибка при обработке")):
            result = simple_search(df, "тест")

        assert result.empty
        assert list(result.columns) == list(df.columns)
        assert len(result) == 0

    def test_get_transfers_regex(self, sample_df: pd.DataFrame) -> None:
        """Находит только переводы физлицам с форматом 'Имя Ф.'."""
        new_rows = pd.DataFrame(
            [
                # Валидный перевод
                {"category": "Переводы", "description": "Перевод Валерий А."},
                # Невалидный: нет категории "Переводы"
                {"category": "Супермаркеты", "description": "Перевод Валерий А."},
                # Невалидный: нет формата "Имя Ф."
                {"category": "Переводы", "description": "Перевод ООО Ромашка"},
                # Валидный: другой регистр категории
                {"category": "перевод физическим лицам", "description": "Оплата Сергей З."},
            ]
        )
        df = pd.concat([sample_df, new_rows], ignore_index=True)

        result = search_transfers(df)

        assert len(result) == 2
        assert "Валерий А." in result.iloc[0]["description"]
        assert "Сергей З." in result.iloc[1]["description"]

    def test_search_transfers_error(self, sample_df: pd.DataFrame, monkeypatch: pytest.MonkeyPatch) -> None:
        """При ошибке возвращается пустой DataFrame."""
        broken_df = sample_df.drop(columns=["category"])
        result = search_transfers(broken_df)
        assert result.empty
