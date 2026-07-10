from src.api import get_currency_rates, get_stock_prices
from src.config import DATA_FILE
from src.utils import current_date, greeting_time, load_transaction

# === ПРОВЕРКА КОДА ===
if __name__ == "__main__":

    # current_date, greeting_time, get_currency_rates
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
