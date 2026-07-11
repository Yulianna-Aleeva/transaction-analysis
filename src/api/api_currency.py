from typing import Any, Dict, List

import requests

from src.logs.log_config import USER_SETTINGS, get_logger

logger = get_logger(__name__)


def get_currency_rates() -> List[Dict[str, Any]]:
    """Получает курсы валют из API."""
    url = USER_SETTINGS.get("currency_url", "")
    codes = USER_SETTINGS.get("user_currencies", [])

    if not url or not codes:
        logger.debug("Отсутствуют настройки: %s.", ", ".join(USER_SETTINGS.keys()))
        raise ValueError(f"Отсутствуют настройки: {', '.join(USER_SETTINGS.keys())}.")

    url_with_params = f"{url}?valute={','.join(codes)}"

    try:
        resp = requests.get(url_with_params, timeout=8)
        resp.raise_for_status()
        logger.debug("Статус ответа API: %s", resp.status_code)

        data = resp.json()
        rates_block = data.get("Valute", {})

        result: List[Dict[str, Any]] = []
        for code in codes:
            if code in rates_block:
                rate = round(float(rates_block[code]["Value"]), 2)
                if rate > 0:
                    result.append({"currency": code, "rate": rate})

        logger.debug("Получено валют: %s.\nКурсы: %s.", len(result), result)
        return result

    except requests.RequestException as e:
        logger.exception("Ошибка запроса к API: %s.", e)
        raise ValueError(f"Ошибка запроса к API: {e}.")
