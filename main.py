import pandas as pd

from src.api.api_currency import get_currency_rates
from src.api.api_stocks import get_stock_prices
from src.logs.log_config import DATA_FILE
from src.reports.expenses_reports import (
    expenses_by_category,
    expenses_by_weekday,
    expenses_work_vs_weekend,
)
from src.services.search_services import simple_search
from src.utils.data_loader import load_transaction
from src.utils.dates_utils import current_date, greeting_time
from src.utils.filters_utils import filter_last_3_months, get_top_positions

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
    query = "Duty услугиc"
    # --- --- --- --- --- ---
    result = simple_search(df, query)
    print(f"Найдено строк: {len(result)}")
    print(result.to_string(index=False))

    print("\nТраты по категориям:")
    print(expenses_by_category(filter_last_3_months).to_string(index=False))

    print("\nТраты по дням недели:")
    print(expenses_by_weekday(filter_last_3_months).to_string(index=False))

    print("\nРабочие/выходные:")
    print(expenses_work_vs_weekend(filter_last_3_months).to_string(index=False))
