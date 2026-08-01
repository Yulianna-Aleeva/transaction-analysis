from flask import Flask
from flask import render_template
from flask import request

from src.constants import MESSAGES
from src.services.dashboard_services import build_dashboard_context
from src.services.dashboard_services import cached_currency
from src.services.dashboard_services import cached_stocks
from src.services.dashboard_services import get_initial_dataframe
from src.utils.format_utils import current_date
from src.utils.format_utils import format_rub
from src.utils.format_utils import greeting_time

app = Flask(__name__)
app.jinja_env.filters["format_rub"] = format_rub
DF = get_initial_dataframe()


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    ctx = build_dashboard_context(DF, request)
    ctx.update(
        currency_rates=cached_currency(),
        stock_prices=cached_stocks(),
        greeting=greeting_time(),
        current_date=current_date(),
        MESSAGES=MESSAGES,
    )
    return render_template("index.html", **ctx)


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
