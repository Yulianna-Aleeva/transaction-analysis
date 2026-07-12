from typing import Any

from flask import Flask, render_template, request

from src.api.api_currency import get_currency_rates
from src.api.api_stocks import get_stock_prices
from src.reports.expenses_reports import (
    expenses_by_category,
    expenses_by_weekday,
    expenses_work_vs_weekend,
)
from src.services.search_services import simple_search
from src.utils.data_loader import load_transaction
from src.utils.filters_utils import filter_last_3_months, get_top_positions
from src.utils.format_utils import current_date, greeting_time

app = Flask(__name__)


@app.route("/")
def index() -> Any:
    """Главная страница."""
    df = load_transaction()
    df_last_3_months = filter_last_3_months(df)

    query = request.args.get("q", "")
    search_result = simple_search(df, query) if query else df.head(0)

    return render_template(
        "index.html",
        greeting=greeting_time(),
        current_date=current_date(),
        currency_rates=get_currency_rates(),
        stock_prices=get_stock_prices(),
        expenses_by_category=expenses_by_category(df_last_3_months).to_dict(orient="records"),
        expenses_by_weekday=expenses_by_weekday(df_last_3_months).to_dict(orient="records"),
        expenses_work_vs_weekend=expenses_work_vs_weekend(df_last_3_months).to_dict(orient="records"),
        top_expenses=get_top_positions(df_last_3_months, "amount_operation", n=5, ascending=True).to_dict(
            orient="records"
        ),
        query=query,
        search_result=search_result.to_dict(orient="records"),
    )


if __name__ == "__main__":
    app.run(debug=True)
