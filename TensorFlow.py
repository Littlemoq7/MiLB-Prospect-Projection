"""Neural-network baseline, kept for comparison. This is NOT the shipped model.

train.py trains what the app serves. This script exists to document why: on 591
rows with 6 features, this network scores at roughly the majority-class
baseline, while the logistic regression in train.py is several points better.

Previously this script evaluated on a single 10% holdout (60 players) and saved
the model whenever it cleared 55% accuracy. That gate was selecting on noise --
across random splits the same architecture ranges from ~42% to ~72%, so re-running
until it "passed" saved whichever split got lucky rather than a better model.

TensorFlow is not installed by requirements.txt (it is ~1.1GB and the app does
not need it). To run this comparison:

    ./mlbvenv/bin/pip install tensorflow==2.18.0
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Input
from tensorflow.keras.optimizers import Adam

FEATURES = ['PA', 'BB%', 'K%', 'ISO', 'GB%', 'wRC+']

data = pd.read_csv('mergedOutput.csv')
X = data[FEATURES].values
y = data['category'].values


def build_model(n_features):
    model = Sequential([
        Input(shape=(n_features,)),
        Dense(32, activation='relu'),
        Dense(16, activation='relu'),
        Dense(8, activation='relu'),
        Dense(3, activation='softmax')
    ])
    model.compile(optimizer=Adam(learning_rate=0.001),
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
    return model


# Same 5-fold stratified CV as train.py, so the two scores are comparable.
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
accuracies = []

for fold, (train_idx, test_idx) in enumerate(cv.split(X, y), start=1):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # Fit the scaler on the training fold only -- fitting on all rows would leak
    # test-fold statistics into training.
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    y_train = tf.keras.utils.to_categorical(y_train - 1, num_classes=3)
    y_test = tf.keras.utils.to_categorical(y_test - 1, num_classes=3)

    model = build_model(X_train.shape[1])
    model.fit(X_train, y_train, epochs=60, batch_size=8, verbose=0)

    _, accuracy = model.evaluate(X_test, y_test, verbose=0)
    accuracies.append(accuracy)
    print(f'fold {fold}: {accuracy * 100:.1f}%')

accuracies = np.array(accuracies)
baseline = pd.Series(y).value_counts(normalize=True).max()

print()
print(f'Majority-class baseline : {baseline * 100:.1f}%')
print(f'5-fold CV accuracy      : {accuracies.mean() * 100:.1f}% (+/- {accuracies.std() * 100:.1f})')
print()
print('Nothing is saved here on purpose -- run train.py to build the served model.')
