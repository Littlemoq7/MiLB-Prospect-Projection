import tensorflow as tf
import pandas as pd
from sklearn.preprocessing import StandardScaler

model = tf.keras.models.load_model('model.keras')
scaler = StandardScaler()
data = pd.read_csv('mergedOutput.csv')
X = data[['PA', 'BB%', 'K%', 'ISO', 'GB%', 'wRC+']].values
scaler = StandardScaler()
scaler.fit_transform(X)


new_player = [[230,0.1,0.29130434699999996,0.14492753600000002,0.449275362,114.00819401335193]] 
new_player = scaler.transform(new_player)
prediction = model.predict(new_player)
predicted_category = prediction.argmax() + 1
print(f"Predicted Category: {predicted_category}")