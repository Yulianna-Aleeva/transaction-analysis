from typing import Dict, Optional

import requests

from logs.config import USER_SETTINGS, get_logger

logger = get_logger(__name__)


def get_currency_rates() -> Dict[str, Optional[float]]:
    """Получает курсы валют и адрес API из настроек в user_settings.json."""
    url = USER_SETTINGS.get("currency_url", "")
    codes = USER_SETTINGS.get("user_currencies", [])
    if not url or not codes:
        logger.debug("Отсутствуют настройки: %s.", ", ".join(USER_SETTINGS.keys()))
        raise ValueError(f"Отсутствуют настройки: {', '.join(USER_SETTINGS.keys())}.")

    url = f"{USER_SETTINGS['currency_url']}?valute={','.join(USER_SETTINGS['user_currencies'])}"

    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        logger.debug("Статус ответа API: %s", resp.status_code)

        data = resp.json()
        rates_block = data.get("Valute", {})

        result: Dict[str, Optional[float]] = {}
        for code in codes:
            if code in rates_block:
                result[code] = round(float(rates_block[code]["Value"]), 2)
            else:
                result[code] = None
        logger.debug("Получено валют: %s.\nКурсы: %s.", len(result), result)

        return result

    except requests.RequestException as e:
        logger.exception("Ошибка запроса к API: %s.", e)
        raise ValueError(f"Ошибка запроса к API: {e}.")
