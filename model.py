import numpy as np
from sklearn.linear_model import LogisticRegression

class MalariaRiskModel:
    def __init__(self):
        # Example training data
        X = np.array([
            [10, 25, 40],  # low risk
            [20, 26, 45],  # low risk
            [50, 28, 55],  # medium risk
            [90, 29, 60],  # medium risk
            [120, 30, 80], # high risk
            [140, 32, 85]  # high risk
        ])
        y = np.array([0, 0, 2, 2, 1, 1])  # 0=low, 2=medium, 1=high

        self.model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=200)
        self.model.fit(X, y)

    def predict(self, features):
        return self.model.predict([features])[0]
