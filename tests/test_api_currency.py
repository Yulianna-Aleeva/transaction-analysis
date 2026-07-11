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
    def test_1_settings_present_success(
        self, mock_get: Mock, default_settings: Dict[str, Any], mock_response_success: Mock
    ) -> None:
        """Тест 1. Настройки присутствуют, запрос успешен."""
        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            mock_get.return_value = mock_response_success
            result = get_currency_rates()

        assert result == {"USD": 75.12, "EUR": 83.0}
        mock_get.assert_called_once()

    def test_2_missing_url(self) -> None:
        """Тест 2. Отсутствует URL."""
        settings = {"user_currencies": ["USD"]}
        with patch(f"{MODULE_PATH}.USER_SETTINGS", settings):
            with pytest.raises(ValueError, match="Отсутствуют настройки"):
                get_currency_rates()

    def test_3_missing_currencies(self) -> None:
        """Тест 3. Нет списка валют."""
        settings = {"currency_url": "http://test.com"}
        with patch(f"{MODULE_PATH}.USER_SETTINGS", settings):
            with pytest.raises(ValueError, match="Отсутствуют настройки"):
                get_currency_rates()

    @patch(f"{MODULE_PATH}.requests.get")
    def test_4_api_error(self, mock_get: Mock, default_settings: Dict[str, Any]) -> None:
        """Тест 4. Ошибка API."""
        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            mock_get.side_effect = requests.RequestException("Connection error")
            with pytest.raises(ValueError, match="Ошибка запроса к API"):
                get_currency_rates()

    @patch(f"{MODULE_PATH}.requests.get")
    def test_5_currency_found(self, mock_get: Mock, default_settings: Dict[str, Any]) -> None:
        """Тест 5. Валюта найдена."""
        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"Valute": {"USD": {"Value": 75.555}}}
            mock_get.return_value = mock_resp

            result = get_currency_rates()

        assert result["USD"] == 75.56

    @patch(f"{MODULE_PATH}.requests.get")
    def test_6_currency_not_found(self, mock_get: Mock, default_settings: Dict[str, Any]) -> None:
        """Тест 6. Валюта не найдена."""
        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"Valute": {"USD": {"Value": 75.5}}}
            mock_get.return_value = mock_resp

            result = get_currency_rates()

        assert result["EUR"] is None

    @patch(f"{MODULE_PATH}.requests.get")
    def test_7_rounding(self, mock_get: Mock, default_settings: Dict[str, Any]) -> None:
        """Тест 7. Округление до 2 знаков."""
        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"Valute": {"USD": {"Value": 75.126}}}
            mock_get.return_value = mock_resp

            result = get_currency_rates()

        assert result["USD"] == 75.13

    @patch(f"{MODULE_PATH}.requests.get")
    @patch(f"{MODULE_PATH}.logger")
    def test_8_logging(
        self, mock_logger: Mock, mock_get: Mock, default_settings: Dict[str, Any], mock_response_success: Mock
    ) -> None:
        """Тест 8. Логирование."""
        with patch(f"{MODULE_PATH}.USER_SETTINGS", default_settings):
            mock_get.return_value = mock_response_success
            get_currency_rates()

        # Проверяем, что логгер был вызван с нужными аргументами
        mock_logger.debug.assert_any_call("Статус ответа API: %s", 200)
        mock_logger.debug.assert_any_call("Получено валют: %s.\nКурсы: %s.", 2, {"USD": 75.12, "EUR": 83.0})
