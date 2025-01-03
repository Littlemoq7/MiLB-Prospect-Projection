import tensorflow as tf
import pandas as pd
from sklearn.preprocessing import StandardScaler

model = tf.keras.models.load_model('model.keras')
scaler = StandardScaler()
data = pd.read_csv('mergedOutput.csv')
X = data[['PA', 'BB%', 'K%', 'ISO', 'GB%', 'wRC+']].values
scaler = StandardScaler()
scaler.fit_transform(X)

milbHitters = pd.read_csv("weightedMiLBStats.csv")

# List of player names
playerNames = ["Roman Anthony", "Walker Jenkins", "Brooks Brannon", "Mike Trout", "Juan Soto"]

# Query players from the list of names
playerPredictList = milbHitters[milbHitters['Name'].isin(playerNames)].values.tolist()

# Predict players in list of players
for player in playerPredictList:
    new_player = [player[1:]]
    new_player = scaler.transform(new_player)
    prediction = model.predict(new_player)
    predicted_category = prediction
    print(f"{player[0]} Predicted Category: {predicted_category}")