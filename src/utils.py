from datetime import datetime
import requests

def greeting_time() -> str:
    """Возвращает приветствие в зависимости от текущего времени суток."""
    current_hour = datetime.now().hour
    if 6 <= current_hour < 12:
        return "Доброе утро"
    elif 12 <= current_hour < 18:
        return "Добрый день"
    elif 18 <= current_hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_currency_rates() -> dict:
    """ Получает курсы валют (сейчас - из ЦБ РФ)."""
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    codes = ["CNY", "USD", "EUR"]
    default_result = {code: None for code in codes}

    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        rates = data.get("Valute", {})

        result = {}
        for code in codes:
            val = rates.get(code)
            if val and "Value" in val:
                result[code] = round(val["Value"], 2)
            else:
                result[code] = None
        return result

    except (requests.RequestException, ValueError, KeyError):

        return default_result
