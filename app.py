import time
from datetime import datetime
from src.utils.messages import MESSAGES

from flask import Flask, render_template, request
import pandas as pd

from src.api.api_currency import get_currency_rates
from src.api.api_stocks import get_stock_prices
from src.logs.log_config import DATA_FILE
from src.reports.expenses_reports import expenses_by_weekday, expenses_by_category, expenses_work_vs_weekend
from src.services.rewards_and_savings import top_cashback_categories
from src.services.search_services import simple_search, search_phone_numbers, search_transfers
from src.utils.data_loader import load_transaction
from src.utils.filters_utils import filter_last_3_months, get_top_positions
from src.utils.format_utils import current_date, greeting_time
from src.utils.messages import MESSAGES
from src.views import get_cards_info, get_events_page_data

app = Flask(__name__, template_folder="templates")

# Кэш для API (обновляется раз в час)
_api_cache = {
    "currency_rates": {"data": None, "time": 0},
    "stock_prices": {"data": None, "time": 0},
}
CACHE_TTL = 3600


def load_data():
    try:
        return load_transaction(DATA_FILE)
    except Exception:
        return None


def get_cached_currency_rates():
    now = time.time()
    if now - _api_cache["currency_rates"]["time"] > CACHE_TTL:
        _api_cache["currency_rates"]["data"] = get_currency_rates()
        _api_cache["currency_rates"]["time"] = now
    return _api_cache["currency_rates"]["data"]


def get_cached_stock_prices():
    now = time.time()
    if now - _api_cache["stock_prices"]["time"] > CACHE_TTL:
        _api_cache["stock_prices"]["data"] = get_stock_prices()
        _api_cache["stock_prices"]["time"] = now
    return _api_cache["stock_prices"]["data"]


def fmt_int(val):
    try:
        return f"{int(round(abs(float(val)))):,}".replace(",", " ")
    except (ValueError, TypeError):
        return "0"


def get_hidden_fields(hide_top7, hide_top5, hide_top3, hide_weekday, hide_workday, custom_end):
    """Вспомогательная функция не нужна, поля передаются прямо в шаблон."""
    pass


@app.route("/", methods=["GET", "POST"])
def index():
    # Сброс при GET
    if request.method == "GET":
        ctx = {
            "greeting": greeting_time(),
            "current_date": current_date(),
            "currency_rates": get_cached_currency_rates(),
            "stock_prices": get_cached_stock_prices(),
            "period_start": "-",
            "period_end": "-",
            "no_data_message": None,
            "invalid_date": False,
            "custom_end": "",
            "hide_top7": False,
            "hide_top5": False,
            "hide_top3": False,
            "hide_weekday": False,
            "hide_workday": False,
            "search_results": [],
            "search_count": 0,
            "search_total": 0,
            "phone_results": [],
            "phone_count": 0,
            "phone_total": 0,
            "phone_error": False,
            "transfer_results": [],
            "transfer_count": 0,
            "transfer_total": 0,
            "top5": [],
            "cards": [],
            "events_data": {"expenses": {"main": [], "transfers_and_cash": []}, "income": {"main": []}},
            "cashback_top": [],
            "weekday_report": [],
            "category_report": [],
            "workday_report": [],
            "messages": MESSAGES,
        }
        return render_template("index.html", **ctx)

    df = load_data()
    if df is None:
        return "Ошибка загрузки данных.", 500

    # --- Состояние фильтров ---
    hide_top7 = request.form.get("hide_top7") == "on"
    hide_top5 = request.form.get("hide_top5") == "on"
    hide_top3 = request.form.get("hide_top3") == "on"
    hide_weekday = request.form.get("hide_weekday") == "on"
    hide_workday = request.form.get("hide_workday") == "on"
    custom_end_str = request.form.get("custom_end", "").strip()

    # --- Обработка конечной даты ---
    end_date_filter = None
    invalid_date = False
    if custom_end_str:
        try:
            end_date_filter = pd.to_datetime(custom_end_str, dayfirst=True, errors="raise")
        except Exception:
            invalid_date = True

    df_filtered = df.copy()
    if end_date_filter and not invalid_date:
        df_filtered = df_filtered[df_filtered["date_operation"] <= end_date_filter]

    if df_filtered.empty:
        no_data_message = MESSAGES["NO_DATA"]
        df_3m = df_filtered
    else:
        no_data_message = None
        df_3m = filter_last_3_months(df_filtered)

    period_start = df_3m["date_operation"].min().strftime("%d.%m.%Y") if not df_3m.empty else "-"
    period_end = df_3m["date_operation"].max().strftime("%d.%m.%Y") if not df_3m.empty else "-"

    currency_rates = get_cached_currency_rates()
    stock_prices = get_cached_stock_prices()

    # --- Поиск ---
    search_results, search_count, search_total = [], 0, 0
    phone_results, phone_count, phone_total, phone_error = [], 0, 0, False
    transfer_results, transfer_count, transfer_total = [], 0, 0

    search_query = request.form.get("search", "").strip()
    if search_query:
        res = simple_search(df_filtered, search_query)
        search_results = res.to_dict(orient="records")
        search_count = len(res)
        search_total = fmt_int(res["amount_rub"].sum()) if not res.empty else 0

    phone_query = request.form.get("phone_query", "").strip()
    phone_all = request.form.get("phone_all") == "on"
    if phone_query or phone_all:
        if phone_query and len(
                phone_query.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")) < 10:
            phone_error = True
        else:
            res = search_phone_numbers(df_filtered, phone_query) if phone_query else search_phone_numbers(df_filtered)
            phone_results = res.to_dict(orient="records")
            phone_count = len(res)
            phone_total = fmt_int(res["amount_rub"].sum()) if not res.empty else 0

    transfer_query = request.form.get("transfer_query", "").strip()
    transfer_all = request.form.get("transfer_all") == "on"
    if transfer_query or transfer_all:
        res = search_transfers(df_filtered)
        if transfer_query:
            res = res[res["description"].str.contains(transfer_query, case=False, na=False)]
        transfer_results = res.to_dict(orient="records")
        transfer_count = len(res)
        transfer_total = fmt_int(res["amount_rub"].sum()) if not res.empty else 0

    for tx in search_results + phone_results + transfer_results:
        if "date_operation" in tx:
            tx["date_operation"] = pd.Timestamp(tx["date_operation"]).strftime("%d.%m.%Y")
        tx["amount_rub"] = fmt_int(tx.get("amount_rub", 0))

    # --- Топ-5 расходов ---
    top5_df = df_3m.copy()
    if hide_top5:
        top5_df = top5_df[~top5_df["category"].str.contains("Перевод", case=False, na=False)]
    top5 = get_top_positions(top5_df, "amount_rub", n=5, ascending=True)
    top5_list = top5[["date_operation", "amount_rub", "category", "description"]].to_dict(orient="records")
    for tx in top5_list:
        tx["date_operation"] = pd.Timestamp(tx["date_operation"]).strftime("%d.%m.%Y")
        tx["amount_rub"] = fmt_int(tx["amount_rub"])

    # --- Карты ---
    cards_spent = get_cards_info(df_3m)
    income_by_card = df_3m[df_3m["amount_rub"] > 0].groupby("card_number")["amount_rub"].sum().reset_index()
    income_by_card["last_digits"] = income_by_card["card_number"].str.replace("*", "", regex=False).str.strip().str[-4:]
    income_dict = dict(zip(income_by_card["last_digits"], income_by_card["amount_rub"]))

    cards_full = []
    for card in cards_spent:
        card_copy = card.copy()
        card_copy["total_income"] = fmt_int(income_dict.get(card["last_digits"], 0.0))
        card_copy["total_spent"] = fmt_int(card["total_spent"])
        card_copy["cashback"] = fmt_int(card["cashback"])
        cards_full.append(card_copy)

    # --- События (Топ-7) ---
    events_data = get_events_page_data(period_end + " 23:59:59", df_3m) if not df_3m.empty else {
        "expenses": {"main": [], "transfers_and_cash": []}, "income": {"main": []}}
    if "expenses" in events_data:
        for item in events_data["expenses"]["main"] + events_data["expenses"]["transfers_and_cash"]:
            item["amount"] = fmt_int(item["amount"])
    if "income" in events_data:
        for item in events_data["income"]["main"]:
            item["amount"] = fmt_int(item["amount"])

    # --- Кешбэк ---
    if not df_3m.empty:
        last_date = df_3m["date_operation"].max()
        cashback_top = top_cashback_categories(df_3m, last_date.year, last_date.month)
    else:
        cashback_top = []
    for item in cashback_top:
        item["cashback"] = fmt_int(item["cashback"])

    # --- Отчёты ---
    def process_report(report_df, hide_flag):
        if hide_flag:
            report_df = report_df[~report_df["category"].str.contains("Перевод", case=False, na=False)]
        return report_df

    weekday_rep = expenses_by_weekday(process_report(df_3m, hide_weekday)).to_dict(orient="records")
    for row in weekday_rep: row["Итого расходов"] = fmt_int(row["Итого расходов"])

    category_rep = expenses_by_category(df_3m).to_dict(orient="records")
    for row in category_rep: row["Итого расходов"] = fmt_int(row["Итого расходов"])

    workday_rep = expenses_work_vs_weekend(process_report(df_3m, hide_workday)).to_dict(orient="records")
    for row in workday_rep: row["Итого расходов"] = fmt_int(row["Итого расходов"])

    return render_template(
        "index.html",
        greeting=greeting_time(),
        current_date=current_date(),
        currency_rates=currency_rates,
        stock_prices=stock_prices,
        period_start=period_start,
        period_end=period_end,
        no_data_message=no_data_message,
        invalid_date=invalid_date,
        custom_end=custom_end_str,
        hide_top7=hide_top7,
        hide_top5=hide_top5,
        hide_top3=hide_top3,
        hide_weekday=hide_weekday,
        hide_workday=hide_workday,
        search_results=search_results,
        search_count=search_count,
        search_total=search_total,
        phone_results=phone_results,
        phone_count=phone_count,
        phone_total=phone_total,
        phone_error=phone_error,
        transfer_results=transfer_results,
        transfer_count=transfer_count,
        transfer_total=transfer_total,
        top5=top5_list,
        cards=cards_full,
        events_data=events_data,
        cashback_top=cashback_top,
        weekday_report=weekday_rep,
        category_report=category_rep,
        workday_report=workday_rep,
        messages=MESSAGES,
    )


if __name__ == "__main__":
    app.run(debug=True)