from typing import Any, Dict, List

import requests

from src.logs.log_config import USER_SETTINGS, get_logger

logger = get_logger(__name__)


error_msg = "Отсутствуют настройки: "


def _fetch_rates_dict() -> Dict[str, float]:
    """Загружает все курсы валют из API и возвращает словарь {код: курс}."""
    url = USER_SETTINGS.get("currency_url", "")
    if not url:
        logger.debug("%s%s.", error_msg, ", ".join(USER_SETTINGS.keys()))
        raise ValueError(f"{error_msg} {', '.join(USER_SETTINGS.keys())}.")

    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        rates_block = data.get("Valute", {})

        all_rates: Dict[str, float] = {}
        for code, info in rates_block.items():
            try:
                rate = round(float(info["Value"]), 2)
                if rate > 0:
                    all_rates[code] = rate
            except (KeyError, TypeError, ValueError):
                continue

        logger.debug("Загружено курсов валют: %d", len(all_rates))
        return all_rates

    except requests.RequestException as e:
        logger.exception("Ошибка запроса к API: %s.", e)
        raise ValueError(f"Ошибка запроса к API: {e}.") from e


def get_all_currency_rates() -> Dict[str, float]:
    """Возвращает словарь всех доступных курсов {код: курс}."""
    return _fetch_rates_dict()


def get_currency_rates() -> List[Dict[str, Any]]:
    """Возвращает курсы только тех валют, которые указаны в user_currencies."""
    codes = USER_SETTINGS.get("user_currencies", [])
    if not codes:
        logger.debug("%s%s.", error_msg, ", ".join(USER_SETTINGS.keys()))
        raise ValueError(f"{error_msg} {', '.join(USER_SETTINGS.keys())}.")

    all_rates = _fetch_rates_dict()

    result: List[Dict[str, Any]] = [
        {"currency": code, "rate": rate} for code, rate in all_rates.items() if code in codes
    ]

    logger.debug("Отобрано валют пользователя: %d.", len(result))
    return result
