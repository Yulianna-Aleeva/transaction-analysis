from src.utils import get_currency_rates, current_date, greeting_time

# === ПРОВЕРКА КОДА ===
if __name__ == "__main__":

    # === src.utils ===

    # current_date, greeting_time, get_currency_rates
    print(f"{greeting_time()}, Вас приветствует аналитик банковских операций!")
    print(f"Курс валют на {current_date()}:")
    rates = get_currency_rates()
    for cur, val in rates.items():
        print(f"{cur}: {val}")
