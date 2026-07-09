from src.utils import get_currency_rates

# === ПРОВЕРКА КОДА ===
if __name__ == "__main__":

    # === src.utils ===

    # get_currency_rates()
    rates = get_currency_rates()
    for cur, value in rates.items():
        print(f"{cur}: {value}")
