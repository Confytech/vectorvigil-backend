import numpy as np
from sklearn.linear_model import LogisticRegression

class MalariaRiskModel:
    def __init__(self):
        # Dummy training data: replace with your real dataset later
        X = np.array([[0, 0], [1, 1], [2, 2], [3, 3]])
        y = np.array([0, 0, 1, 1])  # 0=low risk, 1=high risk

        self.model = LogisticRegression()
        self.model.fit(X, y)

    def predict(self, features):
        """Make prediction on processed features"""
        return self.model.predict([features])[0]

# Instantiate globally so it loads once
malaria_model = MalariaRiskModel()
