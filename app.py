from flask import Flask, render_template, request
from src.services.dashboard_services import get_initial_dataframe, build_dashboard_context, cached_currency, cached_stocks
from src.utils.format_utils import format_rub, greeting_time, current_date
from src.constants import MESSAGES

app=Flask(__name__)
app.jinja_env.filters['format_rub']=format_rub
DF=get_initial_dataframe()

@app.route("/",methods=["GET","POST"])
def index():
    try:
        ctx=build_dashboard_context(DF, request)
        ctx.update(currency_rates=cached_currency(),stock_prices=cached_stocks(),
                   greeting=greeting_time(),current_date=current_date(),MESSAGES=MESSAGES)
        return render_template("index.html",**ctx)
    except Exception as e:
        return render_template("index.html",error=str(e),MESSAGES=MESSAGES,greeting=greeting_time(),current_date=current_date())

if __name__=="__main__":
    app.run(debug=False,threaded=True)
