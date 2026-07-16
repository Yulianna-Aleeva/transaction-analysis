from flask import Flask, render_template, request

from src.constants import MESSAGES
from src.services.dashboard_services import (
    build_dashboard_context,
    cached_currency,
    cached_stocks,
    get_initial_dataframe,
)
from src.utils.format_utils import current_date, format_rub, greeting_time

app = Flask(__name__)
app.jinja_env.filters["format_rub"] = format_rub
DF = get_initial_dataframe()


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    try:
        ctx = build_dashboard_context(DF, request)
        ctx.update(
            currency_rates=cached_currency(),
            stock_prices=cached_stocks(),
            greeting=greeting_time(),
            current_date=current_date(),
            MESSAGES=MESSAGES,
        )
        return render_template("index.html", **ctx)
    except Exception as e:
        return render_template(
            "index.html", error=str(e), MESSAGES=MESSAGES, greeting=greeting_time(), current_date=current_date()
        )


if __name__ == "__main__":
    app.run(debug=False, threaded=True)
