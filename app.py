from flask import Flask, render_template, url_for, redirect, session, request, jsonify
from prediction import predict_players

app = Flask(__name__)
app.secret_key = 'Jarren Duran'.encode('utf8')

@app.route('/', methods = ["GET", "POST"])
def predictPlayer():
    error = None
    if request.method == "POST":
        player_name = request.form['player-name'].strip()
        predictions, _ = predict_players([player_name])
        if not predictions:
            error = f'No stats found for "{player_name}". Check the spelling and try again.'
        else:
            session['player_prediction'] = predictions
            return redirect(url_for('playerEval', player_name=player_name))
    return render_template('main.html', error=error)

@app.route('/<player_name>')
def playerEval(player_name):
    player_prediction = session.get('player_prediction')
    if not player_prediction:
        return redirect(url_for('predictPlayer'))
    return render_template('playerEval.html', player_prediction=player_prediction)

@app.route('/api/predict', methods=["POST"])
def apiPredict():
    data = request.get_json(silent=True) or {}
    player_name = (data.get('player_name') or '').strip()
    if not player_name:
        return jsonify({'error': 'player_name is required'}), 400

    predictions, _ = predict_players([player_name])
    if not predictions:
        return jsonify({'error': f'No stats found for "{player_name}". Check the spelling and try again.'}), 404
    return jsonify(predictions[0])

if __name__ == "__main__":
    app.run(debug=True)