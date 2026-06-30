from pathlib import Path

from flask import Flask, render_template

from src.utils import current_date, get_currency_rates, get_top_expenses, greeting_time

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
# Путь к файлу (меняй только тут)
TRANSACTIONS_FILE = BASE_DIR / "data" / "operations.xlsx"


@app.route("/")
def index() -> str:
    return render_template(
        "index.html",
        date_now=current_date(),
        greeting=greeting_time(),
        rates=get_currency_rates(),
        top_expenses=get_top_expenses(str(TRANSACTIONS_FILE)),
    )


if __name__ == "__main__":
    app.run(debug=True)
