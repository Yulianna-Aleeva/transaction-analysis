from src.config import DATA_FILE
from src.utils import current_date, get_currency_rates, greeting_time, load_transaction

# === ПРОВЕРКА КОДА ===
if __name__ == "__main__":

    # === src.utils ===

    # current_date, greeting_time, get_currency_rates
    print(f"{greeting_time()}, Вас приветствует аналитик банковских операций!")
    print(f"Курс валют на {current_date()}:")
    rates = get_currency_rates()
    for cur, val in rates.items():
        print(f"{cur}: {val}")

    # load_transaction
    df = load_transaction(DATA_FILE)
    print(df.head())
    print(df["date_operation"].dtype)
