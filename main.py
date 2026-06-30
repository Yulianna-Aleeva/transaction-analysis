from flask import Flask, render_template
from src.utils import greeting_time

app = Flask(__name__)

@app.route("/")
def index():
    greeting = greeting_time()
    return render_template("index.html", greeting=greeting)



if __name__ == "__main__":
    app.run(debug=True)