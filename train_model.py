# train_model.py
import numpy as np
import pickle
from sklearn.linear_model import LogisticRegression

# Training data with rainfall, temperature, humidity
X = np.array([
    [10, 25, 30],   # Low risk
    [15, 26, 40],   # Low risk
    [50, 30, 55],   # Medium risk
    [70, 31, 60],   # Medium risk
    [200, 34, 80],  # High risk
    [250, 35, 85],  # High risk
])

# Corresponding labels: 0=Low, 2=Medium, 1=High
y = np.array([0, 0, 2, 2, 1, 1])

# Train the model
model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=200)
model.fit(X, y)

# Save (pickle) the model
with open('model/malaria_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("✅ Model trained and saved to model/malaria_model.pkl")

