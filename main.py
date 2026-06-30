# src/main.py

from src.processor import (
    format_date_column,
    load_transactions,
    sort_transactions_by_amount,
)
from src.reports import (
    expenses_by_category,
    expenses_by_weekday,
    expenses_work_vs_weekend,
)
from src.services import search_transactions


def main() -> None:
    file_path = "data/operations.xlsx"
    df = load_transactions(file_path)

    df_sorted = sort_transactions_by_amount(df)
    df_final = format_date_column(df_sorted)

    # --- ТЕСТ: ПРОСТОЙ ПОИСК ---
    print("\n--- ТЕСТ: ПРОСТОЙ ПОИСК (например, по слову 'супермаркет') ---")
    search_result = search_transactions(df_final, "супермаркет")
    if not search_result.empty:
        print(search_result[["date", "Сумма операции", "Категория", "Описание"]].head())
    else:
        print("Ничего не найдено.")

    # --- ТЕСТ ОТЧЁТА: ТРАТЫ ПО ДНЯМ НЕДЕЛИ ---
    print("\n--- ТЕСТ ОТЧЁТА: ТРАТЫ ПО ДНЯМ НЕДЕЛИ ---")
    report_weekday = expenses_by_weekday(df_final)
    print(report_weekday.to_string(index=False))

    # --- ТЕСТ ОТЧЁТА: ТРАТЫ ПО КАТЕГОРИИ ---
    print("\n--- ТЕСТ ОТЧЁТА: ТРАТЫ ПО КАТЕГОРИИ ---")
    report_category = expenses_by_category(df_final)
    print(report_category.to_string(index=False))

    # --- ТЕСТ ОТЧЁТА: РАБОЧИЙ ДЕНЬ vs ВЫХОДНОЙ ---
    print("\n--- ТЕСТ ОТЧЁТА: РАБОЧИЙ ДЕНЬ vs ВЫХОДНОЙ ---")
    # Для этого отчёта нам нужен df_final, в котором уже есть столбец "День недели"
    report_work_weekend = expenses_work_vs_weekend(df_final)
    print(report_work_weekend.to_string(index=False))


if __name__ == "__main__":
    main()
