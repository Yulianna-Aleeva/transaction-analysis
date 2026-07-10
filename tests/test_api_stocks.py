import logging
from typing import Any, Dict
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests

from api import api_stocks
from api.api_stocks import get_stock_prices

MODULE_PATH = "api.api_stocks"
Settings = Dict[str, Any]


@pytest.fixture
def default_settings() -> Settings:
    """Возвращает настройки для тестов."""
    return {
        "trading_url": "https://moex.test",
        "user_stocks": ["AAPL", "SBER"],
    }


def make_moex_response(rows: list[list[Any]]) -> Mock:
    """Создаёт ответ MOEX."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "marketdata": {
            "columns": ["SECID", "LAST"],
            "data": rows,
        }
    }
    return response


def make_yahoo_data(prices: Dict[str, float]) -> pd.DataFrame:
    """Создаёт DataFrame, похожий на ответ yfinance."""
    columns = pd.MultiIndex.from_arrays(
        [
            ["Close"] * len(prices),
            list(prices),
        ]
    )
    return pd.DataFrame([list(prices.values())], columns=columns)


class TestGetStockPrices:
    """Тесты получения цен акций."""

    @patch(f"{MODULE_PATH}.requests.get")
    def test_1_settings_present(
        self,
        mock_get: Mock,
        default_settings: Settings,
    ) -> None:
        """Возвращает цены из MOEX при наличии настроек."""
        mock_get.return_value = make_moex_response([["AAPL", 195.25], ["SBER", 310.4]])

        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            result = get_stock_prices()

        assert result == {"AAPL": 195.25, "SBER": 310.4}
        mock_get.assert_called_once_with(
            "https://moex.test",
            timeout=8,
        )

    def test_2_missing_trading_url(self) -> None:
        """Выбрасывает ошибку при отсутствии trading_url."""
        settings = {"user_stocks": ["AAPL"]}

        with patch(f"{MODULE_PATH}.USER_SETTINGS", settings):
            with pytest.raises(
                ValueError,
                match="Отсутствуют настройки: trading_url или user_stocks",
            ):
                get_stock_prices()

    def test_3_missing_user_stocks(self) -> None:
        """Выбрасывает ошибку при отсутствии user_stocks."""
        settings = {"trading_url": "https://moex.test"}

        with patch(f"{MODULE_PATH}.USER_SETTINGS", settings):
            with pytest.raises(
                ValueError,
                match="Отсутствуют настройки: trading_url или user_stocks",
            ):
                get_stock_prices()

    @patch(f"{MODULE_PATH}.requests.get")
    @patch(f"{MODULE_PATH}.yf.download")
    def test_4_moex_error_yahoo_success(
        self,
        mock_download: Mock,
        mock_get: Mock,
        default_settings: Settings,
    ) -> None:
        """Использует Yahoo при ошибке запроса к MOEX."""
        mock_get.side_effect = requests.ConnectionError("Ошибка соединения")
        mock_download.return_value = make_yahoo_data({"AAPL": 195.25, "SBER": 310.4})

        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            result = get_stock_prices()

        assert result == {"AAPL": 195.25, "SBER": 310.4}
        mock_download.assert_called_once()

    @patch(f"{MODULE_PATH}.requests.get")
    @patch(f"{MODULE_PATH}.yf.download")
    def test_5_partial_moex_yahoo_supplement(
        self,
        mock_download: Mock,
        mock_get: Mock,
        default_settings: Settings,
    ) -> None:
        """Дополняет отсутствующую цену через Yahoo."""
        mock_get.return_value = make_moex_response([["AAPL", None], ["SBER", 310.4]])
        mock_download.return_value = make_yahoo_data({"AAPL": 195.25, "SBER": 310.4})

        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            result = get_stock_prices()

        assert result == {"AAPL": 195.25, "SBER": 310.4}

    @patch(f"{MODULE_PATH}.requests.get")
    @patch(f"{MODULE_PATH}.yf.download")
    def test_6_both_sources_failed(
        self,
        mock_download: Mock,
        mock_get: Mock,
        default_settings: Settings,
    ) -> None:
        """Выбрасывает ошибку при сбое MOEX и Yahoo."""
        mock_get.side_effect = requests.ConnectionError("MOEX недоступен")
        mock_download.side_effect = RuntimeError("Yahoo недоступен")

        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            with pytest.raises(
                ValueError,
                match="Не удалось получить данные ни с MOEX, ни с Yahoo",
            ):
                get_stock_prices()

    @patch(f"{MODULE_PATH}.requests.get")
    def test_7_rounding(
        self,
        mock_get: Mock,
    ) -> None:
        """Округляет цену до двух знаков."""
        settings = {
            "trading_url": "https://moex.test",
            "user_stocks": ["AAPL"],
        }
        mock_get.return_value = make_moex_response([["AAPL", 195.25678]])

        with patch(f"{MODULE_PATH}.USER_SETTINGS", settings):
            result = get_stock_prices()

        assert result == {"AAPL": 195.26}

    @patch(f"{MODULE_PATH}.requests.get")
    @patch(f"{MODULE_PATH}.yf.download")
    @patch(f"{MODULE_PATH}.logger")
    def test_8_invalid_moex_price(
        self,
        mock_logger: Mock,
        mock_download: Mock,
        mock_get: Mock,
    ) -> None:
        """Возвращает None при некорректной цене MOEX."""
        settings = {
            "trading_url": "https://moex.test",
            "user_stocks": ["AAPL"],
        }
        mock_get.return_value = make_moex_response([["AAPL", "N/A"]])
        mock_download.return_value = pd.DataFrame()

        with patch(f"{MODULE_PATH}.USER_SETTINGS", settings):
            result = get_stock_prices()

        assert result == {"AAPL": None}
        mock_logger.debug.assert_any_call(
            "Некорректная цена для %s: %s",
            "AAPL",
            "N/A",
        )

    def test_9_logging(
        self,
        default_settings: Settings,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Проверяет сообщения логирования."""
        moex_response = make_moex_response([["AAPL", None], ["SBER", 310.4]])
        yahoo_data = make_yahoo_data({"AAPL": 195.25, "SBER": 310.4})

        old_propagate = api_stocks.logger.propagate
        api_stocks.logger.propagate = True

        try:
            with (
                patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings),
                patch(
                    f"{MODULE_PATH}.requests.get",
                    return_value=moex_response,
                ),
                patch(
                    f"{MODULE_PATH}.yf.download",
                    return_value=yahoo_data,
                ),
                caplog.at_level(logging.DEBUG),
            ):
                result = get_stock_prices()
        finally:
            api_stocks.logger.propagate = old_propagate

        assert result == {"AAPL": 195.25, "SBER": 310.4}
        assert "MOEX результат:" in caplog.text
        assert "Дозапрос Yahoo для недостающих кодов:" in caplog.text
