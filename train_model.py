import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import pickle
import os

# Sample malaria dataset
data = {
    'rainfall': [120, 80, 140, 50, 130, 70, 90, 160],
    'temperature': [28, 24, 30, 22, 29, 25, 26, 31],
    'humidity': [85, 65, 90, 60, 88, 67, 72, 95],
    'outbreak': [1, 0, 1, 0, 1, 0, 0, 1]
}
df = pd.DataFrame(data)

# Split dataset
X = df[['rainfall', 'temperature', 'humidity']]
y = df['outbreak']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train the model
model = LogisticRegression()
model.fit(X_train, y_train)

# Create model directory if it doesn't exist
os.makedirs('model', exist_ok=True)

# Save the model
with open('model/malaria_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("✅ Model trained and saved to model/malaria_model.pkl")

