import os

from flask import Flask, render_template, url_for, redirect, session, request, jsonify
from prediction import (
    predict_players,
    predict_manual,
    predict_from_seasons,
    search_player_names,
    FEATURES,
    SEASON_FIELDS,
    LEVELS,
)

app = Flask(__name__)
# Falls back to a fresh random key each run -- fine here since the session only
# holds a short-lived prediction within a single process. Set FLASK_SECRET_KEY
# if you need sessions to survive a restart or run multiple worker processes.
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# Short explanations shown under each manual-entry field, since several
# features (percentages as decimals, AgeRelLevel) aren't self-explanatory.
FEATURE_HINTS = {
    'PA': 'Plate appearances',
    'BB%': 'Walk rate as a decimal, e.g. 0.10 for 10%',
    'K%': 'Strikeout rate as a decimal, e.g. 0.22 for 22%',
    'ISO': 'Isolated power (SLG - AVG), e.g. 0.150',
    'GB%': 'Ground ball rate as a decimal, e.g. 0.45 for 45%',
    'wRC+': 'Weighted runs created+, 100 = league average',
    'Age': 'Age during the season, e.g. 21.5',
    'AgeRelLevel': 'Age minus the average age at that level (negative = younger than average)',
}

# Hints for the season-by-season manual entry form (Svelte). AgeRelLevel is
# deliberately absent -- it's derived automatically from Season + Level + Age
# rather than entered, since a user has no way to know it directly.
SEASON_FIELD_HINTS = {
    'Season': 'Year, e.g. 2024',
    'Level': 'Minor-league level',
    'PA': 'Plate appearances that season',
    'BB%': 'Walk rate as a decimal, e.g. 0.10 for 10%',
    'K%': 'Strikeout rate as a decimal, e.g. 0.22 for 22%',
    'ISO': 'Isolated power (SLG - AVG), e.g. 0.150',
    'GB%': 'Ground ball rate as a decimal, e.g. 0.45 for 45%',
    'wRC+': 'Weighted runs created+, 100 = league average',
    'Age': 'Age during that season, e.g. 21.5',
}

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

@app.route('/api/player-names')
def apiPlayerNames():
    return jsonify(search_player_names(request.args.get('q', '')))

@app.route('/api/season-fields')
def apiSeasonFields():
    # Lets the Svelte frontend render the season-entry form from the same
    # field list + hints the backend expects, so they can't drift.
    return jsonify({
        'fields': [{'name': name, 'hint': SEASON_FIELD_HINTS.get(name, '')} for name in SEASON_FIELDS],
        'levels': LEVELS,
    })

@app.route('/api/predict-seasons', methods=["POST"])
def apiPredictSeasons():
    data = request.get_json(silent=True) or {}
    seasons = data.get('seasons')
    if not isinstance(seasons, list) or not seasons:
        return jsonify({'error': 'Enter at least one season.'}), 400

    try:
        rows = [
            {
                'Season': int(season['Season']),
                'Level': season['Level'],
                'PA': float(season['PA']),
                **{col: float(season[col]) for col in ('BB%', 'K%', 'ISO', 'GB%', 'wRC+', 'Age')},
            }
            for season in seasons
        ]
        result = predict_from_seasons(rows)
    except ValueError as err:
        message = str(err) or 'Enter a valid value for every field in each season.'
        return jsonify({'error': message}), 400
    except (KeyError, TypeError):
        return jsonify({'error': 'Enter a valid value for every field in each season.'}), 400

    return jsonify(result)

@app.route('/manual-entry', methods = ["GET", "POST"])
def manualEntry():
    error = None
    result = None
    values = {}
    if request.method == "POST":
        values = {feature: request.form.get(feature, '').strip() for feature in FEATURES}
        try:
            parsed = {feature: float(values[feature]) for feature in FEATURES}
        except ValueError:
            error = 'Enter a numeric value for every stat.'
        else:
            result = predict_manual(parsed)
    return render_template(
        'manualEntry.html',
        error=error,
        result=result,
        values=values,
        features=FEATURES,
        hints=FEATURE_HINTS,
    )

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
    # Port 5000 is squatted by macOS AirPlay Receiver (Control Center) on
    # most Macs, so this uses 5001 instead.
    app.run(debug=True, port=5001)