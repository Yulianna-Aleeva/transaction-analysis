from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
import requests

from src.api.api_currency import get_currency_rates

MODULE_PATH = "src.api.api_currency"


@pytest.fixture
def default_settings() -> Dict[str, Any]:
    """Базовые настройки для тестов."""
    return {"currency_url": "http://test-api.com", "user_currencies": ["USD", "EUR"]}


@pytest.fixture
def mock_response_success() -> Mock:
    """Успешный ответ API."""
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"Valute": {"USD": {"Value": 75.1234}, "EUR": {"Value": 82.999}}}
    return mock_resp


class TestGetCurrencyRates:

    @patch(f"{MODULE_PATH}.requests.get")
    def test_settings_present_success(
        self, mock_get: Mock, default_settings: Dict[str, Any], mock_response_success: Mock
    ) -> None:
        """Настройки присутствуют, запрос успешен."""
        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            mock_get.return_value = mock_response_success
            result = get_currency_rates()

        assert result == [
            {"currency": "USD", "rate": 75.12},
            {"currency": "EUR", "rate": 83.0},
        ]
        mock_get.assert_called_once_with("http://test-api.com", timeout=8)

    def test_missing_url(self) -> None:
        """Отсутствует URL."""
        settings = {"user_currencies": ["USD"]}
        with patch(f"{MODULE_PATH}.USER_SETTINGS", settings):
            with pytest.raises(ValueError, match="Отсутствуют настройки"):
                get_currency_rates()

    def test_missing_currencies(self) -> None:
        """Нет списка валют."""
        settings = {"currency_url": "http://test.com"}
        with patch(f"{MODULE_PATH}.USER_SETTINGS", settings):
            with pytest.raises(ValueError, match="Отсутствуют настройки"):
                get_currency_rates()

    @patch(f"{MODULE_PATH}.requests.get")
    def test_api_error(self, mock_get: Mock, default_settings: Dict[str, Any]) -> None:
        """Ошибка API."""
        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            mock_get.side_effect = requests.RequestException("Connection error")
            with pytest.raises(ValueError, match="Ошибка запроса к API"):
                get_currency_rates()

    @patch(f"{MODULE_PATH}.requests.get")
    def test_currency_found(self, mock_get: Mock, default_settings: Dict[str, Any]) -> None:
        """Валюта найдена."""
        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"Valute": {"USD": {"Value": 75.555}}}
            mock_get.return_value = mock_resp

            result = get_currency_rates()

        assert len(result) == 1
        assert result[0] == {"currency": "USD", "rate": 75.56}

    @patch(f"{MODULE_PATH}.requests.get")
    def test_currency_not_found(self, mock_get: Mock, default_settings: Dict[str, Any]) -> None:
        """Валюта не найдена и не должна попасть в итоговый список."""
        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            mock_resp = Mock()
            mock_resp.status_code = 200
            # API вернул только USD, EUR отсутствует
            mock_resp.json.return_value = {"Valute": {"USD": {"Value": 75.5}}}
            mock_get.return_value = mock_resp

            result = get_currency_rates()

        assert len(result) == 1
        assert result[0] == {"currency": "USD", "rate": 75.5}

    @patch(f"{MODULE_PATH}.requests.get")
    def test_rounding(self, mock_get: Mock, default_settings: Dict[str, Any]) -> None:
        """Округление до 2 знаков."""
        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"Valute": {"USD": {"Value": 75.126}}}
            mock_get.return_value = mock_resp

            result = get_currency_rates()

        assert result[0]["rate"] == 75.13

    @patch(f"{MODULE_PATH}.requests.get")
    @patch(f"{MODULE_PATH}.logger")
    def test_logging(
        self, mock_logger: Mock, mock_get: Mock, default_settings: Dict[str, Any], mock_response_success: Mock
    ) -> None:
        """Логирование."""
        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            mock_get.return_value = mock_response_success
            get_currency_rates()

        # Проверяем, что логгер был вызван с нужными аргументами
        mock_logger.debug.assert_any_call("Загружено курсов валют: %d", 2)
        mock_logger.debug.assert_any_call("Отобрано валют пользователя: %d.", 2)

    @patch(f"{MODULE_PATH}.requests.get")
    def test_invalid_currency_data_skipped(self, mock_get: Mock, default_settings: Dict[str, Any]) -> None:
        """Пропускает валюты с некорректными данными (покрывает except блок)."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "Valute": {
                "USD": {"Value": 75.5},  # корректная
                "EUR": {"Value": "не число"},  # TypeError
                "CNY": {"WrongKey": 11.3},  # KeyError
                "TRY": {"Value": None},  # ValueError / TypeError
            }
        }
        mock_get.return_value = mock_resp

        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            result = get_currency_rates()

        # Должна остаться только одна валидная валюта
        assert len(result) == 1
        assert result[0] == {"currency": "USD", "rate": 75.5}
