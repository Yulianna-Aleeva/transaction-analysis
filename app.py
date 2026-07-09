from flask import Flask, render_template

from src.api import get_currency_rates
from src.utils import current_date, greeting_time

app = Flask(__name__)


@app.route("/")
def index() -> str:
    rates = get_currency_rates()
    date = current_date()
    greeting = greeting_time()

    return render_template("index.html", rates=rates, date=date, greeting=greeting)
