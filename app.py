from flask import Flask, render_template

from src.utils import current_date, get_currency_rates, greeting_time

app = Flask(__name__)


@app.route("/")
def index() -> str:
    rates = get_currency_rates()
    date = current_date()
    greeting = greeting_time()

    return render_template("index.html", rates=rates, date=date, greeting=greeting)
