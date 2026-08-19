"""Trains the Prospect Predictor model.

Uses multinomial logistic regression inside a scikit-learn Pipeline, so the
StandardScaler is fit as part of the model and saved with it. That keeps
training and inference on an identical transform.

Evaluation is 5-fold stratified cross-validation over all rows rather than a
single holdout -- a small test set swings wildly in accuracy depending on the
split, which is far too noisy to make decisions from.

Training data now includes minor leaguers who never reached the majors
(category 0, see CleaningMLBData.py), not just graduates ranked against each
other -- without them the model never saw what actually separates a future
big leaguer from organizational depth.
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ['PA', 'BB%', 'K%', 'ISO', 'GB%', 'wRC+', 'Age', 'AgeRelLevel']
# Model categories are 0/1/2/3; index into this list directly with `category`
CATEGORY_LABELS = ['Did Not Reach MLB', 'Below Average', 'Average', 'Above Average']
MODEL_PATH = 'model.joblib'

data = pd.read_csv('mergedOutput.csv')
X = data[FEATURES].values
y = data['category'].values

# The scaler lives inside the pipeline so cross-validation refits it on each
# training fold only. Fitting it once on all rows would leak test-fold
# statistics into training and inflate the scores below.
#
# class_weight='balanced' matters a lot more now than it used to: "Did Not
# Reach MLB" outnumbers the three graduate classes combined roughly 5 to 1,
# so an unweighted fit could just predict it for everyone and still score
# well on accuracy. If the classification report below still shows the
# graduate classes getting swamped, the next lever is downsampling the
# majority class -- not attempted here since it's a call best made from real
# CV output, not guessed in advance.
model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight='balanced'))

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy')

# Accuracy alone is misleading here: the classes are heavily imbalanced (see
# the class counts printed below), so always guessing the majority class
# already scores well without the model learning anything.
baseline = pd.Series(y).value_counts(normalize=True).max()

print(f'Rows: {len(data)}   class counts: {pd.Series(y).value_counts().sort_index().to_dict()}')
print()
print(f'Majority-class baseline : {baseline * 100:.1f}%')
print(f'5-fold CV accuracy      : {scores.mean() * 100:.1f}% (+/- {scores.std() * 100:.1f})')
print(f'  per fold              : {np.round(scores * 100, 1)}')
print()

# Per-class recall matters more than overall accuracy -- "Above Average" is the
# class the app exists to find, and it is the hardest one.
predictions = cross_val_predict(model, X, y, cv=cv)
print('Confusion matrix (rows = true, cols = predicted):')
print(pd.DataFrame(
    confusion_matrix(y, predictions),
    index=[f'true {label}' for label in CATEGORY_LABELS],
    columns=[f'pred {label}' for label in CATEGORY_LABELS],
))
print()
print(classification_report(y, predictions, target_names=CATEGORY_LABELS, digits=2))

# Refit on every row for the model that actually ships
model.fit(X, y)
joblib.dump({'model': model, 'features': FEATURES, 'labels': CATEGORY_LABELS}, MODEL_PATH)
print(f'Saved {MODEL_PATH} (scaler included)')
