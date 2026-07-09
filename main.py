from src.utils import get_currency_rates, current_date, greeting_time


def main() -> None:
    date = current_date()
    greeting = greeting_time()
    currency = get_currency_rates()