from flask import Flask, render_template, url_for, redirect, session, request
from prediction import predict_players

app = Flask(__name__)
app.secret_key = 'Jarren Duran'.encode('utf8')

@app.route('/', methods = ["GET", "POST"])
def predictPlayer():
    if request.method == "POST":
        player_name = request.form['player-name']
        session['player_prediction'] = predict_players([player_name])
        return redirect(url_for('playerEval', player_name=player_name))
    return render_template('main.html')

@app.route('/<player_name>')
def playerEval(player_name):
    player_prediction = session['player_prediction']
    return render_template('playerEval.html', player_prediction=player_prediction)

if __name__ == "__main__":
    app.run(debug=True)