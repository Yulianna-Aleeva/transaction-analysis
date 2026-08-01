import json

import pandas as pd

from src.api.api_currency import get_currency_rates
from src.api.api_stocks import get_stock_prices
from src.log_config import DATA_FILE
from src.reports.expenses_reports import expenses_by_category
from src.reports.expenses_reports import expenses_by_weekday
from src.reports.expenses_reports import expenses_work_vs_weekend
from src.services.rewards_and_savings import top_cashback_categories
from src.services.search_services import simple_search
from src.utils.data_loader import load_transaction
from src.utils.filters_utils import filter_last_3_months
from src.utils.filters_utils import get_top_positions
from src.utils.format_utils import current_date
from src.utils.format_utils import greeting_time
from src.views import get_main_page_data

# === ПРОВЕРКА КОДА ===
if __name__ == "__main__":

    # greeting_time
    print(f"{greeting_time()}, Вас приветствует аналитик банковских операций!")

    # get_currency_rates, current_date
    print(f"Курс валют на {current_date()}:")
    rates = get_currency_rates()
    for item in rates:
        print(f"{item['currency']}: {item['rate']}")

    # get_stock_prices, current_date
    print(f"Курс акций на {current_date()}:")
    stocks = get_stock_prices()
    for item in stocks:
        print(f"{item['stock']}: {item['price']}")

    # load_transaction
    df = load_transaction(DATA_FILE)
    print(df.head())

    # Главный JSON-ответ
    print("\n[ГЛАВНАЯ СТРАНИЦА (JSON)]")
    date_str = "2021-12-31 23:59:59"
    main_data = get_main_page_data(date_str, df)
    print(json.dumps(main_data, ensure_ascii=False, indent=2, default=str))

    # Простой поиск "simple_search"
    df_raw = pd.read_excel(DATA_FILE)
    query = "Duty услугиc"
    result = simple_search(df_raw, query)
    print(f"Найдено строк: {len(result)}")
    print(result.to_string(index=False))

    # Отчёты "reports.py" за 3 месяца
    df_3m = filter_last_3_months(df)
    start = df_3m["date_operation"].min().strftime("%d.%m.%Y")
    end = df_3m["date_operation"].max().strftime("%d.%m.%Y")
    print(f"\n=== ОТЧЁТЫ за период: {start} — {end} ===")

    print("\nТраты по категориям:")
    print(expenses_by_category(df_3m).to_string(index=False))

    print("\nТраты по дням недели:")
    print(expenses_by_weekday(df_3m).to_string(index=False))

    print("\nРабочие/выходные:")
    print(expenses_work_vs_weekend(df_3m).to_string(index=False))

    # ТОП-5 расходов за 3 месяца
    top_5 = get_top_positions(df_3m, "amount_operation", n=5, ascending=True)
    print("\nТОП-5 расходов за 3 месяца:")
    print(top_5[["date_operation", "amount_operation", "category", "description"]].to_string(index=False))

    # Кешбэк – ТОП-3 категории за последний месяц
    latest_date = df["date_operation"].max()
    cashback_top = top_cashback_categories(df, latest_date.year, latest_date.month)
    print(f"\nТоп-3 категорий по кешбэку за {latest_date.strftime('%m.%Y')}:")
    for item in cashback_top:
        print(f"  {item['category']}: {item['cashback']} руб.")

    # Отображение суммы с копейками
    for _, row in df.head(15).iterrows():
        date_str = row["date_operation"].strftime("%d.%m.%Y")
        print(f"{date_str} | {row['amount_rub_formatted']} | {row['category']} | {row['description']}")
    # Отображение суммы с округлением
    for _, row in df.head(15).iterrows():
        print(
            f"{row['date_operation'].strftime('%d.%m.%Y')} | "
            f"{row['amount_rub_rounded']:>12} | "
            f"{row['category']} | {row['description']}"
        )
