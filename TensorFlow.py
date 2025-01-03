import tensorflow as tf
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Input
from tensorflow.keras.optimizers import Adam

data = pd.read_csv('mergedOutput.csv')

X = data[['PA', 'BB%', 'K%', 'ISO', 'GB%', 'wRC+']].values
y = data['category'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

y_train = tf.keras.utils.to_categorical(y_train - 1, num_classes=3)
y_test = tf.keras.utils.to_categorical(y_test - 1, num_classes=3)

model = Sequential([
    Input(shape=(X_train.shape[1],)),
    Dense(32, activation='relu'),
    Dense(16, activation='relu'),
    Dense(8, activation='relu'),
    Dense(3, activation='softmax')
])

model.compile(optimizer=Adam(learning_rate=0.001), 
              loss='categorical_crossentropy', 
              metrics=['accuracy'])

history = model.fit(X_train, y_train, epochs=60, batch_size=8, validation_data=(X_test, y_test))

test_loss, test_accuracy = model.evaluate(X_test, y_test)
print(f"Test Accuracy: {test_accuracy:.2f}")

if test_accuracy > 0.55:
    model.save("model.keras", overwrite=True, include_optimizer=True)
    print("saved")

milbHitters = pd.read_csv("weightedMiLBStats.csv")

# List of player names
playerNames = ["Roman Anthony", "Walker Jenkins", "Brooks Brannon"]

# Query players from the list of names
playerPredictList = milbHitters[milbHitters['Name'].isin(playerNames)].values.tolist()

# Predict players in list of players
for player in playerPredictList:
    new_player = [player[1:]]
    new_player = scaler.transform(new_player)
    prediction = model.predict(new_player)
    predicted_category = prediction
    print(f"{player[0]} Predicted Category: {predicted_category}")
