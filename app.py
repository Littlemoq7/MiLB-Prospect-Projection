from flask import Flask, render_template, url_for
from prediction import predict_players

app = Flask(__name__)

playerPredictions = predict_players(["Roman Anthony", "Walker Jenkins", "Brooks Brannon", "Mike Trout", "Juan Soto"])

@app.route('/')
def main():
    return render_template('main.html', prediction=playerPredictions)

if __name__ == "__main__":
    app.run(debug=True)