import pandas as pd

from src.api.api_currency import get_currency_rates
from src.api.api_stocks import get_stock_prices
from src.logs.log_config import DATA_FILE
from src.services.search_services import simple_search
from src.utils.data_loader import load_transaction
from src.utils.dates_utils import current_date, greeting_time

# === ПРОВЕРКА КОДА ===
if __name__ == "__main__":

    # greeting_time, current_date, get_currency_rates
    print(f"{greeting_time()}, Вас приветствует аналитик банковских операций!")
    print(f"Курс валют на {current_date()}:")
    rates = get_currency_rates()
    for cur, val in rates.items():
        print(f"{cur}: {val}")

    # current_date, get_stock_prices
    print(f"Курс акций на {current_date()}:")
    rates = get_stock_prices()
    for cur, val in rates.items():
        print(f"{cur}: {val}")

    # load_transaction
    df = load_transaction(DATA_FILE)
    print(df.head())
    print(df["date_operation"].dtype)

    # simple_search
    df = pd.read_excel(DATA_FILE)
    # === ввод для поиска ===
    query = "Duty услуги"
    # --- --- --- --- --- ---
    result = simple_search(df, query)
    print(f"Найдено строк: {len(result)}")
    print(result.to_string(index=False))
