import json
import os
import sqlite3

from flask import Flask, render_template, jsonify
from flask_cors import CORS

#import pandas as pd

app = Flask(__name__,
            static_folder='templates/lib',)

CORS(app)

db_file = os.path.join(os.path.abspath('..'), "adatabase.sqlite3")


@app.route("/")
def index():

    return render_template("index.html")


@app.route("/api")
def data():
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute("SELECT pm1, pm2, time, humidity, temperature FROM aqi") # where datetime(time) >=datetime('now', '-3 Hour')

    rows = cur.fetchall()

    return jsonify(rows)


if __name__ == "__main__":
    app.run(debug=True)
