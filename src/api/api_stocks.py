from typing import Dict, Optional

import requests
import yfinance as yf

from src.logs.log_config import USER_SETTINGS, get_logger

logger = get_logger(__name__)


def get_stock_prices() -> Dict[str, Optional[float]]:
    """Получает цены акций: сначала MOEX, затем Yahoo."""
    url: str = USER_SETTINGS.get("trading_url", "")
    codes: list = USER_SETTINGS.get("user_stocks", [])

    if not url or not codes:
        message = "Отсутствуют настройки: trading_url или user_stocks"
        logger.error(message)
        raise ValueError(message)

    def get_moex() -> Dict[str, Optional[float]]:
        """Получает цены с Мосбиржи."""
        try:
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            data = response.json()
            market_data = data.get("marketdata", {})
            moex_prices: Dict[str, Optional[float]] = {code: None for code in codes}

            columns = market_data.get("columns")
            rows = market_data.get("data")

            if isinstance(columns, list) and isinstance(rows, list):
                if "SECID" in columns and "LAST" in columns:
                    secid_idx = columns.index("SECID")
                    last_idx = columns.index("LAST")
                    for row in rows:
                        if isinstance(row, list) and len(row) > max(secid_idx, last_idx):
                            code = row[secid_idx]
                            price = row[last_idx]
                            if code in moex_prices and price is not None:
                                try:
                                    moex_prices[code] = round(float(price), 2)
                                except (TypeError, ValueError):
                                    logger.debug("Некорректная цена для %s: %s", code, price)
            else:
                for code in codes:
                    stock_info = market_data.get(code, {})
                    if isinstance(stock_info, dict):
                        price = stock_info.get("LAST")
                        if price is not None:
                            try:
                                moex_prices[code] = round(float(price), 2)
                            except (TypeError, ValueError):
                                logger.debug("Некорректная цена для %s: %s", code, price)

            logger.debug("MOEX результат: %s", moex_prices)
            return moex_prices
        except requests.RequestException as moex_err:
            logger.error("Ошибка запроса к MOEX: %s", moex_err)
            raise
        except Exception as moex_err:
            logger.error("Неизвестная ошибка MOEX: %s", moex_err)
            raise

    def get_yahoo() -> Dict[str, Optional[float]]:
        """Получает цены с Yahoo Finance."""
        try:
            data = yf.download(
                codes,
                period="5d",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
            if data.empty:
                raise ValueError("Yahoo Finance вернул пустые данные")

            close_prices = data["Close"]
            yahoo_prices: Dict[str, Optional[float]] = {}

            for code in codes:
                try:
                    if hasattr(close_prices, "columns"):
                        if code in close_prices.columns:
                            series = close_prices[code]
                        elif len(close_prices.columns) == 1:
                            series = close_prices.iloc[:, 0]
                        else:
                            yahoo_prices[code] = None
                            continue
                    else:
                        series = close_prices

                    clean_series = series.dropna()
                    if not clean_series.empty:
                        yahoo_prices[code] = round(float(clean_series.iloc[-1]), 2)
                    else:
                        yahoo_prices[code] = None
                except (AttributeError, KeyError, IndexError, TypeError, ValueError):
                    yahoo_prices[code] = None

            logger.debug("Yahoo результат: %s", yahoo_prices)
            return yahoo_prices
        except Exception as yahoo_err:
            logger.error("Ошибка запроса к Yahoo Finance: %s", yahoo_err)
            raise

    try:
        result = get_moex()
    except Exception as fallback_err:
        logger.warning("MOEX недоступен, переключаемся на Yahoo: %s", fallback_err)
        try:
            result = get_yahoo()
        except Exception as final_err:
            final_message = f"Не удалось получить данные ни с MOEX, ни с Yahoo: {final_err}"
            logger.error(final_message)
            raise ValueError(final_message) from final_err

    missing_codes = [code for code in codes if result.get(code) is None]

    if missing_codes:
        logger.debug("Дозапрос Yahoo для недостающих кодов: %s", missing_codes)
        try:
            yahoo_supplement = get_yahoo()
            for code in missing_codes:
                if yahoo_supplement.get(code) is not None:
                    result[code] = yahoo_supplement[code]
        except Exception as supplement_err:
            logger.error("Ошибка дозапроса Yahoo: %s", supplement_err)

    return result
