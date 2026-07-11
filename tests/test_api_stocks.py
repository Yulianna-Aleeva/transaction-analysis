import logging
from typing import Any, Dict
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests

from src.api import api_stocks
from src.api.api_stocks import get_stock_prices

MODULE_PATH = "src.api.api_stocks"
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
    def test_settings_present(
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

    def test_missing_trading_url(self) -> None:
        """Выбрасывает ошибку при отсутствии trading_url."""
        settings = {"user_stocks": ["AAPL"]}

        with patch(f"{MODULE_PATH}.USER_SETTINGS", settings):
            with pytest.raises(
                ValueError,
                match="Отсутствуют настройки: trading_url или user_stocks",
            ):
                get_stock_prices()

    def test_missing_user_stocks(self) -> None:
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
    def test_moex_error_yahoo_success(
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
    def test_partial_moex_yahoo_supplement(
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
    def test_both_sources_failed(
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
    def test_rounding(
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
    def test_invalid_moex_price(
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

    def test_logging(
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

    @patch(f"{MODULE_PATH}.requests.get")
    def test_moex_alt_format_dict(self, mock_get: Mock, default_settings: Settings) -> None:
        """Обрабатывает альтернативный словарный формат MOEX."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"marketdata": {"AAPL": {"LAST": 195.25}, "SBER": {"LAST": 310.4}}}
        mock_get.return_value = response

        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            result = get_stock_prices()

        assert result == {"AAPL": 195.25, "SBER": 310.4}

    def test_moex_dict_format_invalid_price(self) -> None:
        """Покрывает некорректную цену в альтернативном формате MOEX."""
        settings = {"trading_url": "https://moex.test", "user_stocks": ["AAPL"]}

        response = Mock()
        response.json.return_value = {"marketdata": {"AAPL": {"LAST": "bad"}}}

        with (
            patch(f"{MODULE_PATH}.USER_SETTINGS", settings),
            patch(f"{MODULE_PATH}.requests.get", return_value=response),
            patch(f"{MODULE_PATH}.yf.download", return_value=pd.DataFrame()),
        ):
            result = get_stock_prices()

        assert result == {"AAPL": None}

    def test_moex_unknown_error_yahoo_success(self) -> None:
        """Покрывает неизвестную ошибку MOEX и успешный переход на Yahoo."""
        settings = {"trading_url": "https://moex.test", "user_stocks": ["AAPL"]}

        response = Mock()
        response.json.side_effect = ValueError("bad json")

        yahoo_data = pd.DataFrame({"Close": [195.25]})

        with (
            patch(f"{MODULE_PATH}.USER_SETTINGS", settings),
            patch(f"{MODULE_PATH}.requests.get", return_value=response),
            patch(f"{MODULE_PATH}.yf.download", return_value=yahoo_data),
        ):
            result = get_stock_prices()

        assert result == {"AAPL": 195.25}

    def test_yahoo_single_column_fallback(self) -> None:
        """Покрывает случай, когда Yahoo вернул одну колонку с другим именем."""
        settings = {"trading_url": "https://moex.test", "user_stocks": ["AAPL"]}

        columns = pd.MultiIndex.from_arrays([["Close"], ["OTHER"]])
        yahoo_data = pd.DataFrame([[195.25]], columns=columns)

        with (
            patch(f"{MODULE_PATH}.USER_SETTINGS", settings),
            patch(f"{MODULE_PATH}.requests.get", side_effect=requests.ConnectionError("MOEX down")),
            patch(f"{MODULE_PATH}.yf.download", return_value=yahoo_data),
        ):
            result = get_stock_prices()

        assert result == {"AAPL": 195.25}

    def test_yahoo_no_matching_columns(self) -> None:
        """Покрывает случай, когда Yahoo не вернул нужные тикеры."""
        settings = {"trading_url": "https://moex.test", "user_stocks": ["AAPL", "SBER"]}

        yahoo_data = make_yahoo_data({"MSFT": 100.0, "TSLA": 200.0})

        with (
            patch(f"{MODULE_PATH}.USER_SETTINGS", settings),
            patch(f"{MODULE_PATH}.requests.get", side_effect=requests.ConnectionError("MOEX down")),
            patch(f"{MODULE_PATH}.yf.download", return_value=yahoo_data),
        ):
            result = get_stock_prices()

        assert result == {"AAPL": None, "SBER": None}

    def test_yahoo_invalid_price(self) -> None:
        """Покрывает некорректную цену Yahoo."""
        settings = {"trading_url": "https://moex.test", "user_stocks": ["AAPL"]}

        columns = pd.MultiIndex.from_arrays([["Close"], ["AAPL"]])
        yahoo_data = pd.DataFrame([["bad"]], columns=columns)

        with (
            patch(f"{MODULE_PATH}.USER_SETTINGS", settings),
            patch(f"{MODULE_PATH}.requests.get", side_effect=requests.ConnectionError("MOEX down")),
            patch(f"{MODULE_PATH}.yf.download", return_value=yahoo_data),
        ):
            result = get_stock_prices()

        assert result == {"AAPL": None}

    def test_yahoo_empty_series(self) -> None:
        """Покрывает пустые значения Yahoo по тикеру."""
        settings = {"trading_url": "https://moex.test", "user_stocks": ["AAPL"]}

        columns = pd.MultiIndex.from_arrays([["Close"], ["AAPL"]])
        yahoo_data = pd.DataFrame([[None]], columns=columns)

        with (
            patch(f"{MODULE_PATH}.USER_SETTINGS", settings),
            patch(f"{MODULE_PATH}.requests.get", side_effect=requests.ConnectionError("MOEX down")),
            patch(f"{MODULE_PATH}.yf.download", return_value=yahoo_data),
        ):
            result = get_stock_prices()

        assert result == {"AAPL": None}
